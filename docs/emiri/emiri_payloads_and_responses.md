**Payloads and Response**

**Authentication Cache (Payload):**  
**POST : [https://analytics-qa.iriworldwide.com/emiriconfig/emiri-authentication/user\_authentication](https://analytics-qa.iriworldwide.com/emiriconfig/&"emiri-authentication/user_authentication)**

```json
{
  "channelId": "directline",
  "conversationId": "9zz8DvtkaAq9SeAIIc8y14-us",
  "user_id": "muthuusharani.manikandan@circana.com",
  "polling_flag": "false",
  "channel_id": "msteams",
  "teams_id": "ab51d9df-a4a8-49c3-a7ae-6979f4355400",
  "counter": "0"
}
```

( **Response):**

```json
{
  "data": {
    "hasUnifyDefaults": true,
    "isAuthenticated": true,
    "isValidUser": true,
    "transactionId": ""
  },
  "redirect_url": "",
  "unify_defaults": {
    "email": "muthuusharani.manikandan@circana.com",
    "ldServiceURL": "https://advantageqa2.iriworldwide.com/ld_dev",
    "model": {
      "PANEL": {
        "baseURL": "https://advantageqa2.iriworldwide.com/ld_dev/",
        "modelID": 1138.0,
        "modelName": "IRI_PNL",
        "modelType": "PANEL",
        "unifyURL": "https://advantageqa2.iriworldwide.com/unify-dev/"
      },
      "POS": {
        "baseURL": "https://advantageqa2.iriworldwide.com/ld_dev/",
        "modelID": 1101.0,
        "modelName": "TSV_WB",
        "modelType": "POS",
        "unifyURL": "https://advantageqa2.iriworldwide.com/unify-dev/"
      }
    },
    "phone": "",
    "tenant": "CL1",
    "unifyURL": {
      "appName": "Dev",
      "appUrl": "https://advantageqa2.iriworldwide.com/unify-dev/",
      "envName": "lnx0867p2"
    },
    "userid": "MManik01zcs"
  }
}


```

**IntentCall (Payload):**

**POST : [https://analytics-qa.iriworldwide.com/llmadmin/api/llm/execution](https://analytics-qa.iriworldwide.com/llmadmin/api/&"llm/execution)**

```json
{
  "useCache": true,
  "model": "azure-gpt-4o",
  "config": {
    "templateName": "ee_intent",
    "variables": {
      "context": "",
      "last_model": "",
      "locale": "en-US",
      "report_context": "There is no report context.",
      "runAsync": false,
      "sentence": "what is the sales of pepsi?",
      "unify_env": "lnx0867p2",
      "unify_tenant": "CL1",
      "useCache": false
    }
  },
  "DesignMode": false,
  "userId": "MManik01zcs",
  "channelId": "directline",
  "conversationId": "9zz8DvtkaAq9SeAIIc8y14-us"
}

```

**(Response):**

```json
{
  "continue": "yes",
  "dataset": "POS",
  "entities": [
    "sales",
    "pepsi"
  ],
  "intents": [
    "perform"
  ],
  "restart": true,
  "runEntity": "true",
  "runReport": "true",
  "statement": "Thinking...",
  "vf": false,
  "why": "Direct sales query for a brand, matches 'perform' intent per examples; POS has sales data."
}


Entity_Response (Payload ):
{
  "files": {
    "Geography": "entity_geography_ee v3",
    "Other": "entity_other_ee v3",
    "Product": "entity_product_ee v3"
  },
  "Geography": "Geography",
  "payload": {
    "asyncrun": "false",
    "config": {
      "templateName": "fast_entity.txt",
      "variables": {
        "AS_MODEL": "TSV_WB",
        "context": "Human: what is the sales of pepsi?\n AI: Thinking...\n",
        "hierarchy_levels": "TotalStore, EdibleNonEdible, Department, Aisle, Category, SubCategory, Parent Company, Manufacturer, BRAND_FRANCHISE, Brand, UPC",
        "hierarchy_name": "Standard Hierarchy",
        "intent": "perform ",
        "last_model": "POS",
        "locale": "en-US",
        "runAsync": "false",
        "sentence": "what is the sales of pepsi?",
        "unify_env": "lnx0867p2",
        "unify_tenant": "CL1",
        "useCache": "true"
      }
    },
    "model": "gpt-4o",
    "userId": "MManik01zcs"
  },
  "Product": "Product",
  "report_context": {
    "Geography": "",
    "Other": "",
    "Product": ""
  },
  "runValueFilter": false
}
```

**`Entity_Response (Payload ):`**  
**`POST: https://advantageqa2.iriworldwide.com/alerts-dev/services/alerts/getEmiriEntityResponseProd`**

```json
{
  "files": {
    "Geography": "entity_geography_ee v3",
    "Other": "entity_other_ee v3",
    "Product": "entity_product_ee v3"
  },
  "Geography": "Geography",
  "payload": {
    "asyncrun": "false",
    "config": {
      "templateName": "fast_entity.txt",
      "variables": {
        "AS_MODEL": "TSV_WB",
        "context": "Human: what is the sales of pepsi?\n AI: Thinking...\n",
        "hierarchy_levels": "TotalStore, EdibleNonEdible, Department, Aisle, Category, SubCategory, Parent Company, Manufacturer, BRAND_FRANCHISE, Brand, UPC",
        "hierarchy_name": "Standard Hierarchy",
        "intent": "perform ",
        "last_model": "POS",
        "locale": "en-US",
        "runAsync": "false",
        "sentence": "what is the sales of pepsi?",
        "unify_env": "lnx0867p2",
        "unify_tenant": "CL1",
        "useCache": "true"
      }
    },
    "model": "gpt-4o",
    "userId": "MManik01zcs"
  },
  "Product": "Product",
  "report_context": {
    "Geography": "",
    "Other": "",
    "Product": ""
  },
  "runValueFilter": false
}
```

**Response:**

```json
{
  "code": 1,
  "duration": "3506 ms",
  "entities": [
    {
      "action": "ADD",
      "c": "N",
      "entity": "pepsi",
      "jobSource": "PRODUCT",
      "level": "Unknown",
      "most_current": true,
      "o_entity": "pepsi",
      "qualifier": "",
      "syns": [
        "pepsico",
        "pepsi cola",
        "pepsi soft drink",
        "pepsi beverage",
        "pepsi drink",
        "pepsi regular",
        "pepsi classic",
        "pepsi soda",
        "pepsi pop",
        "pepsi company"
      ],
      "type": "Product"
    }
  ],
  "extraData": {},
  "FILTER duration": "1471 ms",
  "FILTER_Payload": {
    "asyncrun": "false",
    "config": {
      "templateName": "Filter Entities",
      "variables": {
        "AS_MODEL": "TSV_WB",
        "context": "Human: what is the sales of pepsi?\n AI: Thinking...\n",
        "hierarchy_levels": "TotalStore, EdibleNonEdible, Department, Aisle, Category, SubCategory, Parent Company, Manufacturer, BRAND_FRANCHISE, Brand, UPC",
        "hierarchy_name": "Standard Hierarchy",
        "intent": "perform ",
        "last_model": "POS",
        "locale": "en-US",
        "runAsync": "false",
        "sentence": "what is the sales of pepsi?",
        "unify_env": "lnx0867p2",
        "unify_tenant": "CL1",
        "useCache": "true"
      }
    },
    "model": "gpt-4o",
    "userId": "MManik01zcs"
  },
  "FILTER_Result": {
    "code": 1,
    "execution_ended_at": "2025-08-07 11:49:16.772356+00:00",
    "execution_entry_delay": 0.0,
    "execution_started_at": "2025-08-07 11:49:15.353393+00:00",
    "execution_time": null,
    "key": "f51d1d99d5ee1f0811d64cb0d4b7f9b4060cea9e97b469db6942e5570538ebdd",
    "model_execution_time": 0.74,
    "request_execution_time": 0.0,
    "result": {
      "filters": [],
      "why": "No filter keyword found in the User Query, so no filter entities are returned."
    },
    "thread_start_delay": 0.009676,
    "uuid": null,
    "worker_id": "383130b923851e5b1a662501f842f6ea0640c153fa35325d93e737b569a28a3d:14"
  },
  "filters": [],
  "Geography duration": "403 ms",
  "GEOGRAPHY_manager": "LOCAL",
  "Geography_Payload": {
    "asyncrun": "false",
    "config": {
      "templateName": "entity_geography_ee v3",
      "variables": {
        "AS_MODEL": "TSV_WB",
        "context": "Human: what is the sales of pepsi?\n AI: Thinking...\n",
        "hierarchy_levels": "TotalStore, EdibleNonEdible, Department, Aisle, Category, SubCategory, Parent Company, Manufacturer, BRAND_FRANCHISE, Brand, UPC",
        "hierarchy_name": "Standard Hierarchy",
        "intent": "perform ",
        "last_model": "POS",
        "locale": "en-US",
        "report_context": "",
        "runAsync": "false",
        "sentence": "what is the sales of pepsi?",
        "unify_env": "lnx0867p2",
        "unify_tenant": "CL1",
        "useCache": "true"
      }
    },
    "model": "gpt-4o",
    "userId": "MManik01zcs"
  },
  "Geography_Result": {
    "code": 1,
    "execution_ended_at": "2025-08-07 11:49:15.696828+00:00",
    "execution_entry_delay": 0.0,
    "execution_started_at": "2025-08-07 11:49:15.352254+00:00",
    "execution_time": null,
    "key": "b2d941ddf0897dd657f4fe23f2b60f9d0c8d236482ba3c342000ccc633b26b9a",
    "model_execution_time": 0.0,
    "request_execution_time": 0.0,
    "result": {
      "entities": [],
      "manager": "LOCAL",
      "why": "No geography, retailer, or region explicitly referenced in the User Query per Rule 33; only product mentioned."
    },
    "thread_start_delay": 0.010719,
    "uuid": null,
    "worker_id": "383130b923851e5b1a662501f842f6ea0640c153fa35325d93e737b569a28a3d:18"
  },
  "manager": "LOCAL",
  "Other duration": "480 ms",
  "OTHER_manager": "LOCAL",
  "Other_Payload": {
    "asyncrun": "false",
    "config": {
      "templateName": "entity_other_ee v3",
      "variables": {
        "AS_MODEL": "TSV_WB",
        "context": "Human: what is the sales of pepsi?\n AI: Thinking...\n",
        "hierarchy_levels": "TotalStore, EdibleNonEdible, Department, Aisle, Category, SubCategory, Parent Company, Manufacturer, BRAND_FRANCHISE, Brand, UPC",
        "hierarchy_name": "Standard Hierarchy",
        "intent": "perform ",
        "last_model": "POS",
        "locale": "en-US",
        "report_context": "",
        "runAsync": "false",
        "sentence": "what is the sales of pepsi?",
        "unify_env": "lnx0867p2",
        "unify_tenant": "CL1",
        "useCache": "true"
      }
    },
    "model": "gpt-4o",
    "userId": "MManik01zcs"
  },
  "Other_Result": {
    "code": 1,
    "execution_ended_at": "2025-08-07 11:49:15.763994+00:00",
    "execution_entry_delay": 0.0,
    "execution_started_at": "2025-08-07 11:49:15.413337+00:00",
    "execution_time": null,
    "key": "9307cc5d7de42d14dd4b229a36f47a6f79663b48d57fdfe6e033f5016967de01",
    "model_execution_time": 0.0,
    "request_execution_time": 0.0,
    "result": {
      "entities": [],
      "manager": "LOCAL",
      "v": "2",
      "why": "No entities of type Hierarchy Level, Time, Visualizer, Number, or any other non-Product/Geography/Measures type were explicitly referenced in the User Query. The query only asks about 'sales of pepsi', which is a Product entity and should not be included per Rule 36. No Hierarchy Levels (such as Brand, Category, etc.) are mentioned, and there are no explicit requests for time periods, numbers, or visualizations. Therefore, the response is an empty array as required."
    },
    "thread_start_delay": 0.087294,
    "uuid": null,
    "worker_id": "4c1245caacc1382e935d0d332fa1a96732fc435b7fc891c3af393c075f12e285:11"
  },
  "Product duration": "3466 ms",
  "PRODUCT_manager": "LOCAL",
  "Product_Payload": {
    "asyncrun": "false",
    "config": {
      "templateName": "entity_product_ee v3",
      "variables": {
        "AS_MODEL": "TSV_WB",
        "context": "Human: what is the sales of pepsi?\n AI: Thinking...\n",
        "hierarchy_levels": "TotalStore, EdibleNonEdible, Department, Aisle, Category, SubCategory, Parent Company, Manufacturer, BRAND_FRANCHISE, Brand, UPC",
        "hierarchy_name": "Standard Hierarchy",
        "intent": "perform ",
        "last_model": "POS",
        "locale": "en-US",
        "report_context": "",
        "runAsync": "false",
        "sentence": "what is the sales of pepsi?",
        "unify_env": "lnx0867p2",
        "unify_tenant": "CL1",
        "useCache": "true"
      }
    },
    "model": "gpt-4o",
    "userId": "MManik01zcs"
  },
  "Product_Result": {
    "code": 1,
    "execution_ended_at": "2025-08-07 11:49:18.746561+00:00",
    "execution_entry_delay": 0.0,
    "execution_started_at": "2025-08-07 11:49:15.359308+00:00",
    "execution_time": null,
    "key": "5211fef1068f8cf9317d12a4317a4d18ab83e1cf4fb70b2324cd8a1abfd56956",
    "model_execution_time": 2.62,
    "request_execution_time": 0.0,
    "result": {
      "entities": [
        {
          "action": "ADD",
          "c": "N",
          "entity": "pepsi",
          "level": "Unknown",
          "most_current": true,
          "o_entity": "pepsi",
          "qualifier": "",
          "syns": [
            "pepsico",
            "pepsi cola",
            "pepsi soft drink",
            "pepsi beverage",
            "pepsi drink",
            "pepsi regular",
            "pepsi classic",
            "pepsi soda",
            "pepsi pop",
            "pepsi company"
          ],
          "type": "Product"
        }
      ],
      "manager": "LOCAL",
      "why": "Extracted 'pepsi' as a Product entity from the user query per rules 1, 15b, 22, 25, 43. No Report Context or Skill Name exclusions applied. Synonyms generated for brand context."
    },
    "thread_start_delay": 0.012872,
    "uuid": null,
    "worker_id": "4c1245caacc1382e935d0d332fa1a96732fc435b7fc891c3af393c075f12e285:14"
  }
}
```

**Measures call (Payload ):**  
**POST : [https://analytics-qa.iriworldwide.com/llmadmin/api/llm/execution](https://analytics-qa.iriworldwide.com/llmadmin/api/&"llm/execution)**

```json
{
  "measures": [
    {
      "causal": "Total",
      "dataset": "POS",
      "measure": "Dollar Sales",
      "temporal": "Current"
    },
    {
      "causal": "Total",
      "dataset": "POS",
      "measure": "Unit Sales",
      "temporal": "Current"
    },
    {
      "causal": "Total",
      "dataset": "POS",
      "measure": "Volume Sales",
      "temporal": "Current"
    }
  ],
  "orthogonal_dimensions": [],
  "why": "The user asked for sales of Pepsi. Per the rules, when sales are requested, Dollar Sales, Unit Sales, and Volume Sales must be included. No causals or orthogonal dimensions were specified, so only 'Total' causal is used and no orthogonals are added."
}
```

**Response:**

```json
{
  "useCache": "true",
  "model": "azure-gpt-4o",
  "config": "{\"templateName\":\"fast_pos_measure_identifier_ee.txt\",\"variables\":{\"AS_MODEL\":\"TSV_WB\",\"basis_measure\":\"\",\"context\":\" Human: what is the sales of pepsi?\\\\n AI: Thinking...\\\\n\",\"locale\":\"en-US\",\"report_context\":\"There is no report context.\",\"runAsync\":false,\"sentence\":\"what is the sales of pepsi?\",\"unify_tenant\":\"CL1\"}}",
  "DesignMode": "False",
  "userId": "MManik01zcs",
  "channelId": "directline",
  "conversationId": "9zz8DvtkaAq9SeAIIc8y14-us"
}
```

**RunCopilot Async (Payload):**  
**POST : [https://advantageqa2.iriworldwide.com/alerts-dev/services/alerts/runCopilotAsync](https://advantageqa2.iriworldwide.com/alerts-dev/&"services/alerts/runCopilotAsync)**

```json
{
  "baseURL": "https://advantageqa2.iriworldwide.com/ld_dev/",
  "conversation": "Human: what is the sales of pepsi?\nAI: Thinking...\n",
  "entity": {
    "entities": [
      {
        "action": "ADD",
        "c": "N",
        "entity": "pepsi",
        "jobSource": "PRODUCT",
        "level": "Unknown",
        "most_current": true,
        "o_entity": "pepsi",
        "qualifier": "",
        "syns": [
          "pepsico",
          "pepsi cola",
          "pepsi soft drink",
          "pepsi beverage",
          "pepsi drink",
          "pepsi regular",
          "pepsi classic",
          "pepsi soda",
          "pepsi pop",
          "pepsi company"
        ],
        "type": "Product"
      }
    ],
    "filters": [],
    "valueFilters": null
  },
  "intent": {
    "continue": "yes",
    "dataset": "POS",
    "entities": [
      "sales",
      "pepsi"
    ],
    "intents": [
      "perform"
    ],
    "restart": true,
    "runEntity": "true",
    "runReport": "true",
    "statement": "Thinking...",
    "vf": false,
    "why": "Direct sales query for a brand, matches 'perform' intent per examples; POS has sales data."
  },
  "measure": {
    "measures": [
      {
        "causal": "Total",
        "dataset": "POS",
        "measure": "Dollar Sales",
        "temporal": "Current"
      },
      {
        "causal": "Total",
        "dataset": "POS",
        "measure": "Unit Sales",
        "temporal": "Current"
      },
      {
        "causal": "Total",
        "dataset": "POS",
        "measure": "Volume Sales",
        "temporal": "Current"
      }
    ],
    "orthogonal_dimensions": [],
    "why": "The user asked for sales of Pepsi. Per the rules, when sales are requested, Dollar Sales, Unit Sales, and Volume Sales must be included. No causals or orthogonal dimensions were specified, so only 'Total' causal is used and no orthogonals are added."
  },
  "modelID": 1101.0,
  "modelName": "TSV_WB",
  "modelType": "POS",
  "reportDimensionValues": {
    "Causal": [],
    "Geography": [],
    "Measures": [],
    "Parent Company": [],
    "Periodicity": [],
    "Product": [],
    "Time": []
  },
  "tenant": "CL1",
  "transactionID": "",
  "unifyID": "MManik01zcs",
  "unifyURL": "https://advantageqa2.iriworldwide.com/unify-dev/plus/landing/2/",
  "userSentence": "what is the sales of pepsi?"
}
```

**Response:**

```json
{
  "code": 1,
  "selectionDescription": "Here is the analysis I will be running:\n\nProduct (Standard Hierarchy):\nParent Company (level)\nPEPSICO INC-REGULAR SOFT DRINKS\n\nGeography:\nTotal US - Multi Outlet + Conv\n\nTime:\nTrend Times\nLatest 4 Weeks\nLatest 12 Weeks\nLatest 52 Weeks\n\nPeriodicity:\nCurrent\nChange vs YA\n% Change vs YA\n\nMeasures:\nDollar Sales\nUnit Sales\nVolume Sales\n\nCausal:\nTotal",
  "transactionID": "f1db3d84-0aa9-4852-8171-3a46323d76fc"
}
```

**FetchCopilotData (Payload):**  
**POST : [https://advantageqa2.iriworldwide.com/alerts-dev/services/alerts/fetchCopilotData](https://advantageqa2.iriworldwide.com/alerts-dev/&"services/alerts/fetchCopilotData)**

```json

FetchCopilotData (Payload):{
  "transactionID": "f1db3d84-0aa9-4852-8171-3a46323d76fc"
}
```

	

**Response:**

```json
{
  "action": "SUCCESS",
  "answer": "For the latest 4 weeks ending 07-13-25 in Total US - Multi Outlet + Conv, PEPSICO INC-REGULAR SOFT DRINKS achieved $662.8M in dollar sales, with 176.6M units and 61.2M in volume sales.",
  "changeSelectionLink": "https://advantageqa2.iriworldwide.com/unify-dev/apps/ee_shell.html#/emirieverywhere/refiner/f1db3d84-0aa9-4852-8171-3a46323d76fc",
  "code": 1,
  "imageURL": "https://advantageqa2.iriworldwide.com/ld_dev/export/downloadCache?fileLocation=df24adccc9379806_-3763ab68_19882e6fa21_-af8_0.png",
  "link": "https://advantageqa2.iriworldwide.com/unify-dev/plus/landing/2/df24adccc9379806:-3763ab68:19882e6fa21:-b23",
  "reportContext": {
    "Geography": "{\u0022name\u0022:\u0022Total US - Multi Outlet \u002B Conv\u0022,\u0022type\u0022:\u0022Geography\u0022,\u0022level\u0022:\u0022Level 2\u0022}\n{\u0022name\u0022:\u0022PEPSICO INC-REGULAR SOFT DRINKS\u0022,\u0022type\u0022:\u0022Product\u0022,\u0022level\u0022:\u0022Parent Company\u0022}\n{\u0022name\u0022:\u0022Latest 4 Weeks Ending 07-13-25\u0022,\u0022type\u0022:\u0022Time\u0022,\u0022level\u0022:\u0022Year_444_13\u0022}\n{\u0022name\u0022:\u0022Dollar Sales\u0022,\u0022type\u0022:\u0022Measures\u0022,\u0022level\u0022:\u0022\u0022}\n{\u0022name\u0022:\u0022Unit Sales\u0022,\u0022type\u0022:\u0022Measures\u0022,\u0022level\u0022:\u0022\u0022}\n{\u0022name\u0022:\u0022Volume Sales\u0022,\u0022type\u0022:\u0022Measures\u0022,\u0022level\u0022:\u0022\u0022}\n{\u0022name\u0022:\u0022Total\u0022,\u0022type\u0022:\u0022Causal\u0022,\u0022level\u0022:\u0022Level1\u0022}\n{\u0022name\u0022:\u0022Current\u0022,\u0022type\u0022:\u0022Periodicity\u0022,\u0022level\u0022:\u0022\u0022}\n",
    "Other": "",
    "Product": "{\u0022name\u0022:\u0022Total US - Multi Outlet \u002B Conv\u0022,\u0022type\u0022:\u0022Geography\u0022,\u0022level\u0022:\u0022Level 2\u0022}\n{\u0022name\u0022:\u0022PEPSICO INC-REGULAR SOFT DRINKS\u0022,\u0022type\u0022:\u0022Product\u0022,\u0022level\u0022:\u0022Parent Company\u0022}\n{\u0022name\u0022:\u0022Latest 4 Weeks Ending 07-13-25\u0022,\u0022type\u0022:\u0022Time\u0022,\u0022level\u0022:\u0022Year_444_13\u0022}\n{\u0022name\u0022:\u0022Dollar Sales\u0022,\u0022type\u0022:\u0022Measures\u0022,\u0022level\u0022:\u0022\u0022}\n{\u0022name\u0022:\u0022Unit Sales\u0022,\u0022type\u0022:\u0022Measures\u0022,\u0022level\u0022:\u0022\u0022}\n{\u0022name\u0022:\u0022Volume Sales\u0022,\u0022type\u0022:\u0022Measures\u0022,\u0022level\u0022:\u0022\u0022}\n{\u0022name\u0022:\u0022Total\u0022,\u0022type\u0022:\u0022Causal\u0022,\u0022level\u0022:\u0022Level1\u0022}\n{\u0022name\u0022:\u0022Current\u0022,\u0022type\u0022:\u0022Periodicity\u0022,\u0022level\u0022:\u0022\u0022}\n",
    "reportDimensions": "Geography,Product,Time,Measures,Causal,Periodicity",
    "reportDimensionValues": {
      "Causal": [
        {
          "dim": "Causal",
          "fullPath": "Causal.Causal All Outlets : FOLDER.Total",
          "id": ":Level1:71392",
          "key": null,
          "level": "Level1",
          "name": "Total",
          "type": "",
          "userSelected": true
        }
      ],
      "Geography": [
        {
          "dim": "Geography",
          "fullPath": "Geography.Projected GEOGRAPHIES.Total US : FOLDER.Total US - Multi Outlet + Conv",
          "id": ":Level 2:73618244",
          "key": null,
          "level": "Level 2",
          "name": "Total US - Multi Outlet + Conv",
          "type": "",
          "userSelected": true
        }
      ],
      "Measures": [
        {
          "dim": "Measures",
          "fullPath": "Measures.Sales : FOLDER.Dollar Sales",
          "id": "!M2_1",
          "key": null,
          "level": "",
          "name": "Dollar Sales",
          "type": "",
          "userSelected": true
        },
        {
          "dim": "Measures",
          "fullPath": "Measures.Sales : FOLDER.Unit Sales",
          "id": "!M2_2",
          "key": null,
          "level": "",
          "name": "Unit Sales",
          "type": "",
          "userSelected": true
        },
        {
          "dim": "Measures",
          "fullPath": "Measures.Sales : FOLDER.Volume Sales",
          "id": "!M2_3",
          "key": null,
          "level": "",
          "name": "Volume Sales",
          "type": "",
          "userSelected": true
        }
      ],
      "Periodicity": [
        {
          "dim": "Periodicity",
          "fullPath": "Periodicity.Periodicity : FOLDER.Current",
          "id": "1226",
          "key": null,
          "level": "",
          "name": "Current",
          "type": "",
          "userSelected": true
        }
      ],
      "Product": [
        {
          "dim": "Product",
          "fullPath": "Product.Standard Hierarchy.TOTAL STORE.EDIBLE.DEPT-BEVERAGES.AISLE-CARBONATED SOFT DRINKS.CARBONATED BEVERAGES.REGULAR SOFT DRINKS.PEPSICO INC-REGULAR SOFT DRINKS",
          "id": ":Parent Company:4527492:3506815:3506816:3506762:3506881:6124774:6764403",
          "key": null,
          "level": "Parent Company",
          "name": "PEPSICO INC-REGULAR SOFT DRINKS",
          "type": "",
          "userSelected": true
        }
      ],
      "Time": [
        {
          "dim": "Time",
          "fullPath": "Time.Latest Periods : FOLDER.Latest 4 Weeks Ending 07-13-25",
          "id": ":Year_444_13:155050100",
          "key": "latest 4 weeks ending 08-11-24",
          "level": "Year_444_13",
          "name": "Latest 4 Weeks Ending 07-13-25",
          "type": ""
        }
      ]
    },
    "selectionDescription": "Here is the analysis I will be running:\n\nProduct (Standard Hierarchy):\nParent Company (level)\nPEPSICO INC-REGULAR SOFT DRINKS\n\nGeography:\nTotal US - Multi Outlet + Conv\n\nTime:\nTrend Times\nLatest 4 Weeks\nLatest 12 Weeks\nLatest 52 Weeks\n\nPeriodicity:\nCurrent\nChange vs YA\n% Change vs YA\n\nMeasures:\nDollar Sales\nUnit Sales\nVolume Sales\n\nCausal:\nTotal",
    "sentenceID": 802614,
    "transactionID": "f1db3d84-0aa9-4852-8171-3a46323d76fc"
  }
}


```

Intent  
Entities  
Measures  
runCopilotAsync  
fetchCopilotData