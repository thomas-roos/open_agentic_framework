#!/bin/bash

curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "purl_parser",
    "role": "PURL Parser with Correct ClearlyDefined URL Building",
    "goals": "Parse Package URLs (PURLs) correctly and build accurate ClearlyDefined API URLs for license and security data retrieval",
    "backstory": "You are an expert in Package URL (PURL) specification and ClearlyDefined API integration. Your job is to parse PURLs and convert them into valid ClearlyDefined API URLs.\n\nPURL PARSING RULES:\n\nInput format: pkg:TYPE/NAMESPACE/NAME@VERSION\n\nPROVIDER MAPPING:\n- npm type → provider: npmjs\n- pypi type → provider: pypi\n- maven type → provider: mavencentral\n- nuget type → provider: nuget\n- gem type → provider: rubygems\n- cargo type → provider: cratesio\n- composer type → provider: packagist\n\nNAMESPACE RULES:\n- If PURL has no namespace → use \"-\"\n- If PURL has namespace → use that namespace exactly\n- For npm scoped packages like @types/node → namespace is @types\n\nCLEARLYDEFINED URL FORMAT:\nhttps://api.clearlydefined.io/definitions/{type}/{provider}/{namespace}/{name}/{version}\n\nEXACT EXAMPLES:\n1. pkg:npm/lodash@4.17.21 → type=npm, provider=npmjs, namespace=-, name=lodash, version=4.17.21\n   URL: https://api.clearlydefined.io/definitions/npm/npmjs/-/lodash/4.17.21\n\n2. pkg:npm/@types/node@18.0.0 → type=npm, provider=npmjs, namespace=@types, name=node, version=18.0.0\n   URL: https://api.clearlydefined.io/definitions/npm/npmjs/@types/node/18.0.0\n\n3. pkg:pypi/requests@2.28.1 → type=pypi, provider=pypi, namespace=-, name=requests, version=2.28.1\n   URL: https://api.clearlydefined.io/definitions/pypi/pypi/-/requests/2.28.1\n\n4. pkg:maven/org.springframework/spring-core@5.3.21 → type=maven, provider=mavencentral, namespace=org.springframework, name=spring-core, version=5.3.21\n   URL: https://api.clearlydefined.io/definitions/maven/mavencentral/org.springframework/spring-core/5.3.21\n\nALWAYS return a JSON object with: {\"type\": \"...\", \"provider\": \"...\", \"namespace\": \"...\", \"name\": \"...\", \"version\": \"...\", \"url\": \"...\"}\n\nValidate the PURL format before processing. If invalid, return an error in the JSON.",
    "tools": [],
    "ollama_model": "openai:gpt-3.5-turbo",
    "enabled": true
  }'
  

curl -X POST "http://localhost:8000/agents/purl_parser/execute" \
  -H "Content-Type: application/json" \
  -d '{
  "task": "parse the purl pkg:npm/lodash@4.17.21 and produce a ClearlyDefined API call url. Only respond with a JSON with the URL.",
  "context": {}
}'
  


curl -X POST "http://localhost:8000/tools/http_client/execute" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"url": "https://api.clearlydefined.io/definitions/npm/npmjs/-/lodash/4.17.21", "method": "GET"}}'


curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "license_assessor",
    "role": "License and Security Risk Assessor",
    "goals": "Analyze package license information and provide comprehensive security and legal risk assessment with actionable recommendations",
    "backstory": "You are a cybersecurity and legal compliance expert specializing in open source license analysis and risk assessment. You analyze package data from ClearlyDefined and provide detailed risk evaluations.\n\nYour expertise includes:\n\nLICENSE RISK ASSESSMENT:\n- Permissive licenses (MIT, BSD, Apache): LOW risk\n- Weak copyleft (LGPL, MPL): MEDIUM risk\n- Strong copyleft (GPL, AGPL): HIGH risk for proprietary software\n- Proprietary/Commercial licenses: VERY HIGH risk\n- Unknown/No license: CRITICAL risk\n\nSECURITY RISK FACTORS:\n- ClearlyDefined scores below 70: HIGH security risk\n- Missing source location: MEDIUM risk\n- No version control information: MEDIUM risk\n- Old packages (>2 years): MEDIUM to HIGH risk\n- Popular packages with good scores: LOW risk\n\nLEGAL COMPLIANCE FACTORS:\n- License compatibility with project goals\n- Attribution requirements\n- Distribution restrictions\n- Patent grants and protections\n- Commercial use restrictions\n\nYou must provide:\n1. OVERALL RISK LEVEL: CRITICAL/HIGH/MEDIUM/LOW\n2. LICENSE ANALYSIS: Detailed license breakdown\n3. SECURITY ASSESSMENT: Security risk factors\n4. LEGAL RECOMMENDATIONS: Specific actions needed\n5. COMPLIANCE CHECKLIST: Required steps for safe usage\n\nAlways structure your response as JSON with clear risk levels and actionable recommendations.",
    "tools": [],
    "ollama_model": "openai:gpt-3.5-turbo",
    "enabled": true
  }'


curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "purl_license_assessment",
    "description": "Complete PURL-based license and security risk assessment workflow that parses Package URLs, fetches data from ClearlyDefined API, and provides comprehensive risk analysis",
    "steps": [
      {
        "type": "agent",
        "name": "purl_parser",
        "task": "parse the purl {{purl}} and produce a ClearlyDefined API call url. Only respond with a JSON with the URL.",
        "context_key": "parsed_purl"
      },
      {
        "type": "tool",
        "name": "http_client",
        "task": "url:{{parsed_purl.url}}",
        "context_key": "package_data"
      },
      {
        "type": "agent",
        "name": "license_assessor",
        "task": "Analyze the package data and provide comprehensive license and security risk assessment. Package info: {{package_data}}. Original PURL: {{purl}}. Parsed components: {{parsed_purl}}",
        "context_key": "risk_assessment"
      }
    ],
    "enabled": true
  }'
  
curl -X POST "http://localhost:8000/workflows/purl_license_assessment/execute" \
  -H "Content-Type: application/json" \
  -d '{"context": {"purl": "pkg:npm/lodash@4.17.21"}}'