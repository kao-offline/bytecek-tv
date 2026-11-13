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
        script=(UI/'app.js').read_text(encoding='utf-8')
        for name,mime in [('spilled.png','image/png'),('ct24.svg','image/svg+xml'),('chrome.svg','image/svg+xml')]:
            data=base64.b64encode((UI/'icons'/name).read_bytes()).decode()
            script=script.replace('/icons/'+name,f'data:{mime};base64,{data}')
        await page.evaluate(script)
        await page.route('https://www.google.com/s2/**', lambda route: route.abort())
        await page.wait_for_timeout(1500)
        assert await page.locator('.tile').count()==4
        assert await page.locator('.app-icon').evaluate_all('(imgs)=>imgs.every(i=>i.complete && i.naturalWidth>0)')
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
        # Six tiles share the first row; tile seven wraps. Arrow keys follow rows.
        for i in range(5):
            await page.locator('.tile.add').click()
            await page.locator('#shortcut-name').fill(f'Test {i}')
            await page.locator('#shortcut-url').fill(f'https://example.com/{i}')
            await page.locator('#add-form button[type=submit]').click()
        boxes=await page.locator('.tile').evaluate_all('(tiles)=>tiles.map(t=>({x:t.offsetLeft,y:t.offsetTop}))')
        assert len({b['y'] for b in boxes[:6]})==1, boxes
        assert boxes[6]['y']>boxes[0]['y'], boxes
        await page.locator('.tile').first.focus()
        await page.keyboard.press('ArrowDown')
        assert await page.locator('.tile:focus').get_attribute('data-index')=='6'
        await page.keyboard.press('ArrowUp')
        assert await page.locator('.tile:focus').get_attribute('data-index')=='0'
        await page.locator('.tile').first.click()
        assert await page.locator('#launching').is_visible()
        assert await page.locator('#launch-label').inner_text()=='Opening Spilled'
        await page.wait_for_timeout(1100)
        assert not await page.locator('#launching').is_visible()
        for width in (1920,1280,800,480):
            await page.set_viewport_size({'width':width,'height':1080})
            assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert not errs,errs
        print('PASS UI: four default shortcuts; add shortcut; power menu; confirmation; exit; Escape; no page errors')
        await browser.close()

asyncio.run(main())
