"""Inspecciona como la Store API expone productos variables y sus variaciones."""
import asyncio
import json

import httpx


async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            "https://avelectronics.cc/wp-json/wc/store/v1/products",
            params={"per_page": 10, "search": "Capacitor Electrolítico 25V"},
        )
        for p in r.json():
            print(f"id={p['id']} type={p.get('type')} name={p['name']}")
            if p.get("type") == "variable":
                print(f"  variations: {p.get('variations')}")
                print(f"  attributes: {json.dumps(p.get('attributes'), ensure_ascii=False)[:400]}")
                # Probar fetch de una variacion individual
                var_ids = p.get("variations") or []
                if var_ids:
                    vid = var_ids[0] if isinstance(var_ids[0], int) else var_ids[0].get("id")
                    rv = await client.get(
                        f"https://avelectronics.cc/wp-json/wc/store/v1/products/{vid}"
                    )
                    print(f"  variacion {vid}: status={rv.status_code}")
                    if rv.status_code == 200:
                        v = rv.json()
                        print(f"    name={v.get('name')}")
                        print(f"    variation={v.get('variation')}")
                        print(f"    price={v.get('prices', {}).get('price')} stock={v.get('is_in_stock')}")


asyncio.run(main())
