from typing import List, Optional
from pydantic import BaseModel

class ProviderAddress(BaseModel):
    address_1: str
    city: str
    state: str
    postal_code: str
    country_code: str
    telephone_number: Optional[str] = None

class ProviderTaxonomy(BaseModel):
    code: str
    desc: Optional[str] = None
    primary: bool
    state: Optional[str] = None
    license: Optional[str] = None

class ProviderResult(BaseModel):
    npi: str
    full_name: str
    enumeration_type: str
    primary_taxonomy: Optional[str] = None
    primary_specialty: Optional[str] = None
    primary_address: Optional[ProviderAddress] = None

class SearchProviderRequest(BaseModel):
    query: str
    state: Optional[str] = None
    taxonomy: Optional[str] = None

class SearchProviderResponse(BaseModel):
    results: List[ProviderResult]

class ProviderDetail(BaseModel):
    npi: str
    full_name: str
    enumeration_type: str
    taxonomies: List[ProviderTaxonomy]
    addresses: List[ProviderAddress]
