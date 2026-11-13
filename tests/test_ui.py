#!/usr/bin/env python3
"""UI smoke test using in-memory markup (works in sandboxed browsers)."""
import asyncio
import base64
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
UI=ROOT/'ui'

async def main():
    html=(UI/'index.html').read_text(encoding='utf-8')
    svg=base64.b64encode((UI/'b.svg').read_bytes()).decode()
    html=html.replace('<link rel="stylesheet" href="/style.css">',f'<style>{(UI/"style.css").read_text(encoding='utf-8')}</style>')
    html=html.replace('<script src="/app.js" defer></script>','')
    html=html.replace('src="/b.svg"',f'src="data:image/svg+xml;base64,{svg}"')
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=['--no-sandbox'])
        page=await browser.new_page(viewport={'width':1440,'height':1080})
        errs=[]
        page.on('pageerror',lambda e: errs.append(str(e)))
        await page.set_content(html)
        await page.evaluate("""() => {
          const mem={};
          Object.defineProperty(window, 'localStorage', {configurable:true,value:{getItem:k=>mem[k]||null,setItem:(k,v)=>{mem[k]=v;}}});
          window.fetch=async()=>({json:async()=>({token:'test-token'}),ok:true});
        }""")
        await page.evaluate((UI/'app.js').read_text(encoding='utf-8'))
        await page.wait_for_timeout(1500)
        assert await page.locator('.tile').count()==4
        await page.screenshot(path=str(ROOT/'preview.png'),full_page=True)
        await page.locator('.tile.add').click()
        assert await page.locator('#add-modal').is_visible()
        await page.locator('#shortcut-name').fill('My service')
        await page.locator('#shortcut-url').fill('https://example.com')
        await page.locator('#add-form button[type=submit]').click()
        assert await page.locator('.tile').count()==5
        await page.locator('#power-toggle').click()
        assert await page.locator('#power-panel').is_visible()
        await page.locator('[data-power=suspend]').click()
        assert await page.locator('#confirm').is_visible()
        await page.locator('#confirm-no').click()
        assert not await page.locator('#confirm').is_visible()
        await page.locator('#exit').click()
        assert await page.locator('#confirm').is_visible()
        await page.keyboard.press('Escape')
        assert not await page.locator('#confirm').is_visible()
        assert not errs,errs
        print('PASS UI: four default shortcuts; add shortcut; power menu; confirmation; exit; Escape; no page errors')
        await browser.close()

asyncio.run(main())
