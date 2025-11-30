import httpx
from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from .schemas_npi import SearchProviderRequest, SearchProviderResponse, ProviderResult, ProviderAddress, ProviderDetail, ProviderTaxonomy

app = FastAPI(title="NPI_API")

NPPES_API_URL = "https://npiregistry.cms.hhs.gov/api/"
NPPES_VERSION = "2.1"

def _map_address(addr_data: dict) -> ProviderAddress:
    return ProviderAddress(
        address_1=addr_data.get("address_1", ""),
        city=addr_data.get("city", ""),
        state=addr_data.get("state", ""),
        postal_code=addr_data.get("postal_code", ""),
        country_code=addr_data.get("country_code", ""),
        telephone_number=addr_data.get("telephone_number")
    )

def _map_taxonomy(tax_data: dict) -> ProviderTaxonomy:
    return ProviderTaxonomy(
        code=tax_data.get("code", ""),
        desc=tax_data.get("desc"),
        primary=tax_data.get("primary", False),
        state=tax_data.get("state"),
        license=tax_data.get("license")
    )

@app.post("/search_providers", response_model=SearchProviderResponse)
async def search_providers(request: SearchProviderRequest):
    params = {
        "version": NPPES_VERSION,
        "limit": 10  # default limit
    }

    # Heuristic: if query looks like a number and length is 10, treat as NPI.
    # Otherwise treat as name or generic search term.
    # The prompt says "query", but NPPES requires specific fields.
    # We'll map 'query' to 'organization_name' or 'first_name'/'last_name' logic
    # could be complex. For simplicity, let's try to map it to 'number' if digit,
    # or partial name search.
    # Actually, often users want to search by name.

    if request.query.isdigit() and len(request.query) == 10:
        params["number"] = request.query
    else:
        # If it has a space, assume first/last name
        if " " in request.query:
            parts = request.query.split(" ", 1)
            params["first_name"] = parts[0]
            params["last_name"] = parts[1]
        else:
            # Fallback to organization name or last name
            # This is ambiguous, but let's try organization name first?
            # Or just last name? Let's use last_name as it's common for individual providers
            # Or maybe try a broad search if possible?
            # NPPES doesn't have a generic "q" parameter.
            # Let's try setting last_name if it looks like a name.
            params["last_name"] = request.query
            # Also could be organization_name
            # params["organization_name"] = request.query # Can't do both usually in one query simply

    if request.state:
        params["state"] = request.state
    if request.taxonomy:
        params["taxonomy_description"] = request.taxonomy

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(NPPES_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"NPPES API error: {str(e)}")

    results = []
    if "results" in data:
        for item in data["results"]:
            basic = item.get("basic", {})
            full_name = f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip()
            if not full_name:
                full_name = basic.get("organization_name", "")

            # Get primary address (location)
            addresses = item.get("addresses", [])
            primary_addr_data = next((a for a in addresses if a.get("address_purpose") == "LOCATION"), None)
            if not primary_addr_data and addresses:
                primary_addr_data = addresses[0]

            primary_addr = _map_address(primary_addr_data) if primary_addr_data else None

            # Get primary taxonomy
            taxonomies = item.get("taxonomies", [])
            primary_tax = next((t for t in taxonomies if t.get("primary") is True), None)
            primary_spec = primary_tax.get("desc") if primary_tax else None
            primary_tax_code = primary_tax.get("code") if primary_tax else None

            results.append(ProviderResult(
                npi=str(item.get("number")),
                full_name=full_name,
                enumeration_type=item.get("enumeration_type", ""),
                primary_taxonomy=primary_tax_code,
                primary_specialty=primary_spec,
                primary_address=primary_addr
            ))

    return SearchProviderResponse(results=results)

@app.get("/provider/{npi}", response_model=ProviderDetail)
async def get_provider(npi: str):
    params = {
        "version": NPPES_VERSION,
        "number": npi
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(NPPES_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"NPPES API error: {str(e)}")

    if "results" not in data or not data["results"]:
        raise HTTPException(status_code=404, detail="Provider not found")

    item = data["results"][0]
    basic = item.get("basic", {})
    full_name = f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip()
    if not full_name:
        full_name = basic.get("organization_name", "")

    taxonomies = [_map_taxonomy(t) for t in item.get("taxonomies", [])]
    addresses = [_map_address(a) for a in item.get("addresses", [])]

    return ProviderDetail(
        npi=str(item.get("number")),
        full_name=full_name,
        enumeration_type=item.get("enumeration_type", ""),
        taxonomies=taxonomies,
        addresses=addresses
    )
