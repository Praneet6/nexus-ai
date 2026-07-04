import sys
import os
import asyncio

# Add backend directory to path to reuse embedding and Pinecone models
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.append(backend_dir)

from dotenv import load_dotenv
# Load env variables from the root .env
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))

from app.config import get_settings
from app.ai.collective_memory import get_pinecone_index, store_resolved_query

DEMO_PATTERNS = [
    {
        "query_text": "Where is my delivery? Order ID IN-84021. It has been delayed for two days.",
        "resolution_text": "Checked status for order IN-84021. It is PACKED and delayed due to local customs clearance issues. Initiated priority dispatch status via BlueDart.",
        "next_issue": "delivery address mismatch or contact number update request"
    },
    {
        "query_text": "I want a refund for my order. The shoe size is too small.",
        "resolution_text": "Initiated a full refund of ₹2,499 for order shoe return. Refund ID REF938201. Advised customer to drop off the package at the nearest DHL point.",
        "next_issue": "refund status check or courier pickup delay"
    },
    {
        "query_text": "My account is locked and I cannot sign in. Please reset my password.",
        "resolution_text": "Triggered password reset email link to the customer email address. Confirmed verification link remains active for 24 hours.",
        "next_issue": "verification email not received or link expired"
    },
    {
        "query_text": "Can I get a discount code or coupon for my next purchase?",
        "resolution_text": "Generated and applied a ₹500 discount coupon (code: NEXUSSAVE500) to customer's profile as customer loyalty reward.",
        "next_issue": "coupon code invalid at checkout or expired coupon"
    },
    {
        "query_text": "My order was delivered but the screen is cracked. I need to exchange it.",
        "resolution_text": "Approved instant exchange order for damaged goods. Scheduled courier pickup for the damaged item and overnight shipping of replacement.",
        "next_issue": "courier did not show up for pickup"
    },
    {
        "query_text": "I paid twice for my transaction and got charged double. Help!",
        "resolution_text": "Identified duplicate payment gateway transaction. Refunded the secondary transaction of ₹1,850. Refund ID REF581903.",
        "next_issue": "refund reflection delay in banking system"
    }
]

async def seed_data():
    settings = get_settings()
    if not settings.pinecone_api_key:
        print("❌ Error: PINECONE_API_KEY is not set in your .env file.")
        return

    print("🔌 Connecting to Pinecone...")
    try:
        index = get_pinecone_index(settings.pinecone_api_key, settings.pinecone_index)
        if index is None:
            raise ValueError("Failed to create/get index.")
    except Exception as e:
        print(f"❌ Connection to Pinecone failed: {e}")
        return

    print(f"🌱 Seeding {len(DEMO_PATTERNS)} resolved cases into Pinecone index '{settings.pinecone_index}'...")
    for pattern in DEMO_PATTERNS:
        success = await store_resolved_query(
            query_text=pattern["query_text"],
            resolution_text=pattern["resolution_text"],
            next_issue=pattern["next_issue"],
            pinecone_index=index
        )
        if success:
            print(f"✅ Upserted pattern: \"{pattern['query_text'][:40]}...\"")
        else:
            print(f"❌ Failed to upsert pattern: \"{pattern['query_text'][:40]}...\"")

    print("🎉 Pinecone seeding completed!")

if __name__ == "__main__":
    asyncio.run(seed_data())
