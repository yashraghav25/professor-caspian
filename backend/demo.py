"""
End-to-End Demo Script
Triggers the 'rapid_crash' simulation to demonstrate SentinelAI's autonomous processing.
"""

import httpx
import asyncio
import sys

async def run_demo():
    print("🚀 Starting SentinelAI Demo...")
    
    async with httpx.AsyncClient(base_url="http://localhost:8000/api") as client:
        # 1. Check if backend is up
        try:
            res = await client.get("/portfolio")
            if res.status_code != 200:
                print("❌ Backend is not running or returned an error.")
                return
        except Exception:
            print("❌ Could not connect to backend. Please ensure it is running on port 8000.")
            return
            
        print("✅ Connected to SentinelAI Backend.")
        
        # 2. Start simulation
        print("⏳ Triggering 'rapid_crash' market simulation...")
        res = await client.post("/simulation/start/rapid_crash")
        if res.status_code == 200:
            print("✅ Simulation started successfully.")
        else:
            print(f"❌ Failed to start simulation: {res.text}")
            return
            
        # 3. Monitor alerts
        print("👀 Monitoring alerts for 15 seconds...\n")
        for _ in range(15):
            res = await client.get("/alerts")
            alerts = res.json()
            if alerts:
                top_alert = alerts[0]
                print(f"🚨 ALERT: [{top_alert['severity_level']}] {top_alert['title']} (Score: {top_alert['severity_score']})")
                print(f"   Reason: {top_alert['reason']}")
            else:
                print("   No active alerts yet...")
                
            await asyncio.sleep(2)
            
        print("\n🎉 Demo completed. Check your dashboard at http://localhost:3000 to see the final state!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_demo())
