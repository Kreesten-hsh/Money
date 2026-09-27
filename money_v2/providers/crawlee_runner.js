/**
 * crawlee_runner.js — Exécuteur Node.js pour Crawlee (Money V2)
 * Reçoit un fichier JSON de configuration (URLs, concurrency, maxRetries, timeoutSec)
 * et produit un JSON de résultats normalisé.
 */

const fs = require('fs');
const path = require('path');

async function run() {
    const args = process.argv.slice(2);
    if (args.length < 2) {
        console.error("Usage: node crawlee_runner.js <input.json> <output.json>");
        process.exit(1);
    }

    const inputPath = args[0];
    const outputPath = args[1];

    const inputData = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));
    const urls = inputData.urls || [];
    const maxConcurrency = inputData.concurrency || 3;
    const maxRetries = inputData.maxRetries || 2;
    const timeoutSec = inputData.timeoutSec || 10;

    let crawlee;
    try {
        crawlee = require('crawlee');
    } catch (e) {
        console.error("MODULE_NOT_FOUND: crawlee is not installed in node_modules.");
        process.exit(2);
    }

    const results = {
        total_urls: urls.length,
        successful: [],
        failed: [],
        items: []
    };

    const crawler = new crawlee.CheerioCrawler({
        maxConcurrency: maxConcurrency,
        maxRequestRetries: maxRetries,
        requestHandlerTimeoutSecs: timeoutSec,
        async requestHandler({ request, $, log }) {
            const pageTitle = $('title').text().trim();
            const metaDesc = $('meta[name="description"]').attr('content') || '';
            results.items.push({
                url: request.url,
                status_code: 200,
                title: pageTitle,
                meta_desc: metaDesc,
                retries: request.retryCount
            });
            results.successful.push(request.url);
        },
        async failedRequestHandler({ request, log }) {
            results.failed.push({
                url: request.url,
                error_message: request.errorMessages ? request.errorMessages.join('; ') : 'Failed'
            });
        }
    });

    await crawler.run(urls);
    fs.writeFileSync(outputPath, JSON.stringify(results, null, 2), 'utf-8');
}

run().catch(err => {
    console.error("Crawler error:", err);
    process.exit(1);
});
