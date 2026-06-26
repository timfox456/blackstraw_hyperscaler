import json

def generate_a2ui_json(
    batch_name: str,
    audience_name: str,
    product_name: str,
    time_name: str,
    measure_name: str,
    consumer_count_millions: str
) -> str:
    html_content = f"""<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset='UTF-8'>
  <meta content="connect-src 'none'" http-equiv="Content-Security-Policy">
  <title>Batch Details</title>
  <style>
    body {{ font-family: sans-serif; background-color: #0f172a; color: #f8fafc; padding: 15px; margin: 0; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); max-width: 600px; margin: 0 auto; overflow: hidden; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #334155; }}
    .header h2 {{ font-size: 18px; font-weight: 600; margin: 0; color: #f1f5f9; }}
    .close-btn {{ color: #94a3b8; font-size: 20px; cursor: pointer; background: none; border: none; }}
    .content {{ padding: 20px; }}
    .field-label {{ font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }}
    .batch-name {{ font-size: 20px; font-weight: 600; color: #f1f5f9; margin-bottom: 20px; word-break: break-all; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 24px; }}
    .grid-card {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 12px; }}
    .grid-val {{ font-size: 14px; font-weight: 500; color: #e2e8f0; display: flex; align-items: center; gap: 6px; margin-top: 4px; }}
    .pill {{ display: inline-flex; align-items: center; border-radius: 9999px; padding: 2px 8px; font-size: 12px; font-weight: 500; }}
    .pill-green {{ background-color: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }}
    .pill-grey {{ background-color: #1e293b; color: #cbd5e1; border: 1px solid #475569; display: inline-block; margin-right: 6px; margin-top: 4px; padding: 4px 10px; border-radius: 6px; font-size: 13px; }}
    .section-title {{ font-size: 12px; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; margin-bottom: 12px; margin-top: 24px; }}
    .audience-box {{ border: 1px solid #334155; border-radius: 8px; padding: 16px; background: #0f172a; }}
    .aud-name {{ font-size: 15px; font-weight: 600; color: #f1f5f9; margin-bottom: 12px; word-break: break-all; }}
    .badges-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }}
    .badge {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 4px 10px; font-size: 12px; color: #cbd5e1; display: flex; gap: 4px; }}
    .badge span {{ color: #f1f5f9; font-weight: 600; }}
    .badge-green {{ background-color: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.3); color: #34d399; }}
    .nested-group {{ margin-bottom: 12px; }}
    .nested-group:last-child {{ margin-bottom: 0; }}
    .footer {{ display: flex; justify-content: flex-end; gap: 12px; padding: 12px 20px; background: #0f172a; border-top: 1px solid #334155; }}
    .btn {{ padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; }}
    .btn-secondary {{ background: none; border: 1px solid #475569; color: #94a3b8; }}
    .btn-primary {{ background: #3b82f6; border: none; color: white; }}
  </style>
</head>
<body>
  <div class='card'>
    <div class='header'>
      <h2>Batch Details</h2>
      <button class='close-btn'>&times;</button>
    </div>
    <div class='content'>
      <div class='field-label'>Batch Name</div>
      <div class='batch-name'>{batch_name}</div>
      
      <div class='grid'>
        <div class='grid-card'>
          <div class='field-label'>Status</div>
          <div class='grid-val'>
            <span class='pill pill-green'>Sized</span>
          </div>
        </div>
        <div class='grid-card'>
          <div class='field-label'>Author</div>
          <div class='grid-val'>Vijay Kallepalli</div>
        </div>
        <div class='grid-card'>
          <div class='field-label'>Last Updated</div>
          <div class='grid-val'>June 24, 2026</div>
        </div>
      </div>

      <div class='section-title'>AUDIENCES</div>
      <div class='audience-box'>
        <div class='aud-name'>{audience_name}</div>
        <div class='badges-row'>
          <div class='badge'>Definition: <span>Buyers</span></div>
          <div class='badge'>Type: <span>Verified</span></div>
          <div class='badge'>Est. Count: <span>{consumer_count_millions}</span></div>
          <div class='badge badge-green'>Status: <span>Sized</span></div>
        </div>

        <div class='nested-group'>
          <div class='field-label'>PRODUCTS</div>
          <span class='pill pill-grey'>{product_name}</span>
        </div>

        <div class='nested-group'>
          <div class='field-label'>TIME</div>
          <span class='pill pill-grey'>{time_name}</span>
        </div>

        <div class='nested-group'>
          <div class='field-label'>MEASURES</div>
          <span class='pill pill-grey'>{measure_name}</span>
        </div>
      </div>
    </div>
    <div class='footer'>
      <button class='btn btn-secondary'>Edit</button>
      <button class='btn btn-primary'>Close</button>
    </div>
  </div>
</body>
</html>"""

    # Escape all double quotes inside the htmlContent literal string
    escaped_html = html_content.replace('"', '\\"')
    
    a2ui_payload = [
        {
            "beginRendering": {
                "surfaceId": "liquid-activation-batch-details",
                "root": "details-root"
            }
        },
        {
            "surfaceUpdate": {
                "surfaceId": "liquid-activation-batch-details",
                "components": [
                    {
                        "webFrameSrcdoc": {
                            "htmlContent": {
                                "literalString": escaped_html
                            },
                            "height": 550
                        }
                    }
                ]
            }
        }
    ]
    
    return f"<a2ui-json>\n{json.dumps(a2ui_payload, indent=2)}\n</a2ui-json>"

if __name__ == "__main__":
    # Test variables matching the latest successful run:
    output_a2ui = generate_a2ui_json(
        batch_name="Orchestrator A2A Sizing Batch 11117f7a",
        audience_name="a2a_sizing_audience_11117f7a",
        product_name="COCA COLA CO LOW CALORIE SOFT DRINKS",
        time_name="Latest 13 Weeks Ending 06-14-26",
        measure_name="Dollars > $0",
        consumer_count_millions="7.33M"
    )
    print(output_a2ui)
