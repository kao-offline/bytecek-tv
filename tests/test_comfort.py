"""Validate comfort styles without loading the external Spilled service."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    script=(Path(__file__).resolve().parents[1]/'browser-extension/comfort.js').read_text(encoding='utf-8')
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        for host,reduced in [('spilled.kaooffline.top',True),('example.com',False)]:
            page=await browser.new_page()
            await page.add_init_script(script)
            await page.route('**/*',lambda r:r.fulfill(content_type='text/html',body='<html><head><style>html{background:rgb(100, 110, 120)}div{animation:test 2s infinite}@keyframes test{to{opacity:0.5}}</style></head><body><div>Content</div></body></html>'))
            await page.goto('https://'+host)
            assert await page.evaluate('getComputedStyle(document.documentElement).backgroundColor')=='rgb(100, 110, 120)'
            duration=await page.locator('div').evaluate('el=>getComputedStyle(el).animationDuration')
            assert (duration=='1e-05s')==reduced, duration
            await page.close()
        await browser.close()
    print('PASS comfort: loading canvas removed; motion reduced only on Spilled')

asyncio.run(main())
