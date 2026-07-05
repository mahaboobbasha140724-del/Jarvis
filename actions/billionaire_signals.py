import os
import sys
from pathlib import Path
from datetime import datetime

def _get_mongo_uri():
    paths = [
        Path(r'C:\Users\Shaik Nabi Rasool\OneDrive\Desktop\trade\backend\.env'),
        Path(__file__).resolve().parent.parent.parent / "trade" / "backend" / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / "trade" / "backend" / ".env"
    ]
    for p in paths:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if 'MONGO_URI' in line:
                        parts = line.strip().split('=', 1)
                        if len(parts) == 2:
                            return parts[1].strip('"').strip("'")
            except Exception:
                pass
    return None

def billionaire_signals(parameters=None, player=None, **kwargs):
    """
    Query or post trading signals to the Billionaire Signals website database (MongoDB).
    """
    if isinstance(parameters, str):
        parameters = {"action": "list"}
    if not isinstance(parameters, dict):
        return "Error: Invalid parameters format."

    action = parameters.get("action", "list").lower()
    
    try:
        from pymongo import MongoClient
        from bson import ObjectId
    except ImportError:
        return "Error: pymongo or bson library not found. Run: pip install pymongo"

    uri = _get_mongo_uri()
    if not uri:
        return "Error: Could not locate trade project MONGO_URI in C:\\Users\\Shaik Nabi Rasool\\OneDrive\Desktop\\trade\\backend\\.env"

    try:
        client = MongoClient(uri)
        db = client.get_default_database()
        signals_col = db["signals"]
        
        if action == "list":
            signals = list(signals_col.find().sort("createdAt", -1).limit(10))
            if not signals:
                return "No signals found on the Billionaire Signals database."
            
            lines = ["### Live Signals on Billionaire Signals:"]
            for s in signals:
                lines.append(
                    f"- **{s.get('stockName')}** ({s.get('type')}) | Entry: {s.get('entryPrice')} | Target: {s.get('target')} | SL: {s.get('stopLoss')} | Status: {s.get('status')} | Expiry: {s.get('expiry')} | ID: {s.get('_id')}"
                )
            return "\n".join(lines)
            
        elif action == "post":
            stock_name = parameters.get("stock_name", "").strip().upper()
            sig_type = parameters.get("type", "").strip().upper()
            entry_price = parameters.get("entry_price")
            stop_loss = parameters.get("stop_loss")
            target = parameters.get("target")
            expiry = parameters.get("expiry", "").strip() or datetime.now().strftime("%b %Y").upper()
            contract = parameters.get("contract", "").strip()
            status = parameters.get("status", "ACTIVE").strip().upper()
            
            card_image_url = parameters.get("card_image_url", "").strip()
            if not card_image_url:
                card_image_url = "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=600&q=80"
            
            if not stock_name or sig_type not in ["BUY", "SELL"] or not entry_price or not stop_loss or not target:
                return "Error: Missing required fields: stock_name, type (BUY/SELL), entry_price, stop_loss, target."

            new_sig = {
                "stockName": stock_name,
                "contract": contract,
                "type": sig_type,
                "entryPrice": float(entry_price),
                "stopLoss": float(stop_loss),
                "target": float(target),
                "expiry": expiry,
                "status": status,
                "cardImageUrl": card_image_url,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow(),
                "__v": 0
            }
            
            res = signals_col.insert_one(new_sig)
            msg = f"Successfully posted signal for **{stock_name}** to Billionaire Signals! ID: {res.inserted_id}"
            if player:
                player.write_log(f"[Billionaire Signals] Posted {sig_type} for {stock_name}")
            return msg
            
        elif action == "delete":
            signal_id = parameters.get("signal_id", "").strip()
            stock_name = parameters.get("stock_name", "").strip().upper()
            
            if signal_id:
                res = signals_col.delete_one({"_id": ObjectId(signal_id)})
            elif stock_name:
                res = signals_col.delete_many({"stockName": stock_name})
            else:
                return "Error: Specify signal_id or stock_name to delete."
                
            if res.deleted_count > 0:
                return f"Successfully deleted {res.deleted_count} signal(s) from Billionaire Signals."
            return "No matching signal found to delete."
            
        else:
            return f"Error: Unknown action '{action}'"
            
    except Exception as e:
        return f"Error connecting to Billionaire Signals database: {str(e)}"
