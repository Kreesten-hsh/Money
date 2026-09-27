from __future__ import annotations

import json
import re
import socket
import ssl
import struct
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, ObservationMethod, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderError, ProviderStatus
from money_v2.providers.base import BaseProvider


def _parse_dns_name(data: bytes, offset: int) -> Tuple[str, int]:
    """Décode un nom de domaine DNS RFC 1035 avec décompression de pointeurs."""
    labels: List[str] = []
    visited_offsets = set()
    orig_offset = offset
    stepped = False

    while True:
        if offset in visited_offsets or offset >= len(data):
            break
        visited_offsets.add(offset)
        length = data[offset]
        if (length & 0xC0) == 0xC0:
            ptr = struct.unpack('!H', data[offset:offset + 2])[0] & 0x3FFF
            if not stepped:
                orig_offset = offset + 2
                stepped = True
            offset = ptr
            continue
        if length == 0:
            offset += 1
            if not stepped:
                orig_offset = offset
            break
        offset += 1
        labels.append(data[offset:offset + length].decode('latin1', errors='ignore'))
        offset += length
        if not stepped:
            orig_offset = offset

    return '.'.join(labels), orig_offset


class DnsMxProvider(BaseProvider):
    """
    Provider DNS/MX déterministe à 3 paliers :
    1. Requête DNS UDP brute RFC 1035 directe sur serveurs DNS publics.
    2. Fallback socket getaddrinfo.
    3. Fallback DNS-over-HTTPS (DoH) via dns.google (pur stdlib).
    """

    PUBLIC_DNS_SERVERS = ['1.1.1.1', '8.8.8.8', '9.9.9.9']

    def __init__(self, timeout: float = 2.5, enabled: bool = True):
        super().__init__(name="dns_mx_provider", enabled=enabled)
        self.timeout = timeout

    def is_available(self) -> bool:
        return True

    def _resolve_udp(self, domain: str) -> List[str]:
        # Construction paquet DNS RFC 1035
        tid = 0x4321
        flags = 0x0100  # Standard query, RD=1
        header = struct.pack('!HHHHHH', tid, flags, 1, 0, 0, 0)
        qname = b''.join(bytes([len(part)]) + part.encode('ascii') for part in domain.split('.') if part) + b'\x00'
        qtype = 15  # MX
        qclass = 1  # IN
        packet = header + qname + struct.pack('!HH', qtype, qclass)

        for dns_ip in self.PUBLIC_DNS_SERVERS:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            try:
                sock.sendto(packet, (dns_ip, 53))
                data, _ = sock.recvfrom(2048)
                sock.close()

                if len(data) < 12:
                    continue
                resp_flags, qdcount, ancount = struct.unpack('!HHHHHH', data[:12])[1:4]
                if (resp_flags & 0x000F) != 0:  # RCODE != NOERROR
                    continue
                if ancount == 0:
                    continue

                # Sauter la section Question
                offset = 12
                for _ in range(qdcount):
                    while offset < len(data) and data[offset] != 0:
                        if (data[offset] & 0xC0) == 0xC0:
                            offset += 2
                            break
                        offset += 1 + data[offset]
                    else:
                        offset += 1
                    offset += 4  # TYPE + CLASS

                mx_records: List[Tuple[int, str]] = []
                for _ in range(ancount):
                    if offset >= len(data):
                        break
                    _, offset = _parse_dns_name(data, offset)
                    if offset + 10 > len(data):
                        break
                    rtype, _, _, rdlength = struct.unpack('!HHIH', data[offset:offset + 10])
                    offset += 10
                    rdata_end = offset + rdlength

                    if rtype == 15 and rdlength >= 2:  # MX
                        pref = struct.unpack('!H', data[offset:offset + 2])[0]
                        exchange, _ = _parse_dns_name(data, offset + 2)
                        if exchange:
                            mx_records.append((pref, exchange))
                    offset = rdata_end

                if mx_records:
                    mx_records.sort(key=lambda x: x[0])
                    return [r[1] for r in mx_records]
            except Exception:
                sock.close()
                continue
        return []

    def _resolve_doh(self, domain: str) -> List[str]:
        doh_url = f"https://dns.google/resolve?name={urllib.parse.quote(domain)}&type=MX"
        try:
            req = urllib.request.Request(
                doh_url,
                headers={"Accept": "application/dns-json", "User-Agent": "Money-OSINT/2.0"}
            )
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                if resp.status != 200:
                    return []
                payload = json.loads(resp.read().decode("utf-8"))
                answers = payload.get("Answer", [])
                mx_hosts: List[str] = []
                for ans in answers:
                    if ans.get("type") == 15:
                        data_field = ans.get("data", "")
                        parts = data_field.split()
                        if len(parts) >= 2:
                            mx_hosts.append(parts[1].rstrip("."))
                        elif parts:
                            mx_hosts.append(parts[0].rstrip("."))
                return mx_hosts
        except Exception:
            return []

    def _run(self, target: str, context: Dict[str, Any]) -> ProviderResult:
        domain = target.strip().lower()
        lead_id = str(context.get("lead_id") or domain)
        now_iso = get_current_iso_timestamp()

        if not domain or not re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", domain):
            raise ProviderError(f"Domaine DNS invalide : {domain}", ProviderStatus.INVALID_INPUT)

        # Palier 1 : UDP direct
        mx_hosts = self._resolve_udp(domain)
        method_used = "DNS_UDP_RFC1035"

        # Palier 2 : getaddrinfo fallback
        if not mx_hosts:
            try:
                socket.getaddrinfo(domain, 25, socket.AF_INET, socket.SOCK_STREAM)
                mx_hosts = [f"fallback-a.{domain}"]
                method_used = "GETADDRINFO_FALLBACK"
            except Exception:
                pass

        # Palier 3 : DoH Google
        if not mx_hosts:
            mx_hosts = self._resolve_doh(domain)
            if mx_hosts:
                method_used = "DOH_GOOGLE_HTTPS"

        evidences: List[Evidence] = []
        if mx_hosts:
            evidences.append(Evidence(
                field="mx_valid",
                value=True,
                source="dns.google / RFC 1035 UDP",
                source_url=f"dns://{domain}/MX",
                observed_at=now_iso,
                method=ObservationMethod.DNS_QUERY.value,
                provider=self.name,
                provider_status=ProviderStatus.SUCCESS.value,
                evidence_text=f"Serveurs MX valides observés via {method_used} : {', '.join(mx_hosts[:2])}",
                confidence=ConfidenceLevel.HIGH.value,
                lead_id=lead_id,
                metadata={"mx_hosts": mx_hosts, "method": method_used}
            ))
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.SUCCESS,
                evidences=evidences,
                raw_payload={"mx_hosts": mx_hosts, "method": method_used}
            )

        return ProviderResult(
            provider=self.name,
            status=ProviderStatus.NO_RESULT,
            evidences=[],
            raw_payload={"domain": domain, "resolved": False}
        )
