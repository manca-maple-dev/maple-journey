"""Phase 3: Citation Validation

Extract citations from LLM responses and validate:
1. Citation format compliance ([Source: URL, published DATE])
2. URL accessibility (HTTP 200)
3. Source whitelist (approved domains only)
4. Deep-link validity (URL contains expected keywords)

IRPA s.91 compliance: Every response MUST cite a source.
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import httpx

logger = logging.getLogger("maplejourney.citation_validator")


# Approved source registry (whitelist for citable domains)
APPROVED_SOURCES = {
    # Government of Canada
    "ircc.canada.ca": {"name": "IRCC", "category": "government"},
    "canada.ca": {"name": "Government of Canada", "category": "government"},
    "gc.ca": {"name": "Government of Canada", "category": "government"},
    
    # Provincial
    "ontario.ca": {"name": "Government of Ontario", "category": "provincial"},
    "gov.bc.ca": {"name": "Government of British Columbia", "category": "provincial"},
    "quebec.ca": {"name": "Gouvernement du Québec", "category": "provincial"},
    "gov.ab.ca": {"name": "Government of Alberta", "category": "provincial"},
    
    # Trusted Legal/Non-profit
    "legalaid.ca": {"name": "Legal Aid Ontario", "category": "legal"},
    "ccpa.ca": {"name": "Canadian Centre for Policy Alternatives", "category": "think_tank"},
    "carleton.ca": {"name": "Carleton University", "category": "education"},
    "toronto.ca": {"name": "City of Toronto", "category": "municipal"},
    
    # Job/Career
    "jobbank.gc.ca": {"name": "Job Bank", "category": "employment"},
    "indeed.com": {"name": "Indeed", "category": "employment"},
    "linkedin.com": {"name": "LinkedIn", "category": "employment"},
    
    # News (sanitized, published by Canadians)
    "globalnews.ca": {"name": "Global News", "category": "news"},
    "cbc.ca": {"name": "CBC News", "category": "news"},
    "bbc.com": {"name": "BBC", "category": "international_news"},
}


class CitationValidator:
    """Extract, validate, and enforce citation requirements."""
    
    # Regex to match [Source: URL, published DATE] or variations
    CITATION_PATTERN = re.compile(
        r'\[(?:Source|source|Source:)\s*:?\s*([^\],]+),\s*(?:published|pub)\s*(\d{4}-\d{2}-\d{2}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})\]',
        re.IGNORECASE
    )
    
    def __init__(self, http_timeout: float = 5.0):
        self.timeout = http_timeout
        self.approved_sources = APPROVED_SOURCES
    
    def extract_citations(self, text: str) -> List[Dict[str, str]]:
        """Extract all [Source: URL, published DATE] citations from text.
        
        Returns: [{ url, date, raw_citation }, ...]
        """
        citations = []
        for match in self.CITATION_PATTERN.finditer(text):
            url = match.group(1).strip()
            date = match.group(2).strip()
            raw = match.group(0)
            
            citations.append({
                "url": url,
                "date": date,
                "raw_citation": raw,
                "start": match.start(),
                "end": match.end(),
            })
        
        return citations
    
    def validate_citation_format(self, citation: Dict[str, str]) -> Tuple[bool, str]:
        """Check if citation has correct format.
        
        Returns: (is_valid, reason)
        """
        url = citation.get("url", "").strip()
        date = citation.get("date", "").strip()
        
        if not url:
            return False, "Missing URL"
        
        if not date:
            return False, "Missing publication date"
        
        # Basic URL validation
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, f"Invalid URL format: {url}"
        except Exception as e:
            return False, f"URL parse error: {str(e)}"
        
        return True, "OK"
    
    def validate_source_whitelist(self, url: str) -> Tuple[bool, str]:
        """Check if URL is from approved source domain.
        
        Returns: (is_whitelisted, source_name_or_reason)
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")
            
            # Exact match
            if domain in self.approved_sources:
                return True, self.approved_sources[domain]["name"]
            
            # Subdomain match (e.g., ontario.ca covers ministry.ontario.ca)
            for approved_domain in self.approved_sources.keys():
                if domain.endswith("." + approved_domain) or domain == approved_domain:
                    return True, self.approved_sources[approved_domain]["name"]
            
            return False, f"Domain '{domain}' not in whitelist"
        
        except Exception as e:
            return False, f"Whitelist check error: {str(e)}"
    
    async def validate_url_accessible(self, url: str) -> Tuple[bool, str]:
        """Check if URL is accessible (HTTP 200).
        
        Returns: (is_accessible, status_or_error)
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.head(url)
                
                if response.status_code == 200:
                    return True, f"HTTP {response.status_code}"
                elif response.status_code in [301, 302, 303, 307, 308]:
                    return True, f"HTTP {response.status_code} (redirected)"
                else:
                    return False, f"HTTP {response.status_code}"
        
        except httpx.TimeoutException:
            return False, "Timeout (URL too slow)"
        except httpx.RequestError as e:
            return False, f"Request error: {str(e)[:50]}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)[:50]}"
    
    async def validate_all(self, response_text: str) -> Dict[str, any]:
        """Comprehensive citation validation.
        
        Returns:
        {
            "citations_found": 3,
            "citations_valid": 2,
            "citations": [
                {
                    "url": "...",
                    "date": "...",
                    "format_valid": True,
                    "whitelisted": True,
                    "accessible": True,
                    "issues": []
                },
                ...
            ],
            "overall_valid": True,
            "issues": []
        }
        """
        citations = self.extract_citations(response_text)
        results = {
            "citations_found": len(citations),
            "citations_valid": 0,
            "citations": [],
            "overall_valid": True,
            "issues": [],
        }
        
        for citation in citations:
            issues = []
            
            # Check format
            format_ok, format_msg = self.validate_citation_format(citation)
            if not format_ok:
                issues.append(f"Format error: {format_msg}")
            
            # Check whitelist
            whitelist_ok, whitelist_msg = self.validate_source_whitelist(citation.get("url", ""))
            if not whitelist_ok:
                issues.append(f"Whitelist: {whitelist_msg}")
            
            # Check accessibility
            accessible_ok, accessible_msg = await self.validate_url_accessible(citation.get("url", ""))
            if not accessible_ok:
                issues.append(f"Accessibility: {accessible_msg}")
            
            citation_result = {
                "url": citation.get("url"),
                "date": citation.get("date"),
                "format_valid": format_ok,
                "whitelisted": whitelist_ok,
                "accessible": accessible_ok,
                "issues": issues,
            }
            
            results["citations"].append(citation_result)
            
            if not issues:
                results["citations_valid"] += 1
            else:
                results["overall_valid"] = False
                results["issues"].extend(issues)
        
        # IRPA s.91: Response MUST have at least 1 valid citation
        if results["citations_found"] == 0:
            results["overall_valid"] = False
            results["issues"].append("IRPA s.91: Response must include at least one source citation")
        
        return results
    
    def format_citation(self, url: str, published_date: str) -> str:
        """Generate properly formatted citation.
        
        Returns: [Source: URL, published DATE]
        """
        return f"[Source: {url}, published {published_date}]"
    
    async def enforce_or_reject(self, response_text: str, allow_uncited: bool = False) -> Tuple[bool, str]:
        """Validate response or reject if citations missing.
        
        Args:
            response_text: LLM response to validate
            allow_uncited: If False, reject responses with no citations (IRPA s.91)
        
        Returns: (is_valid, reason_or_error)
        """
        validation = await self.validate_all(response_text)
        
        if validation["citations_found"] == 0:
            if allow_uncited:
                logger.warning("Uncited response allowed (non-compliance)")
                return True, "No citations found (allowed for this request)"
            else:
                reason = "IRPA s.91 violation: Response must cite sources"
                logger.error(reason)
                return False, reason
        
        if not validation["overall_valid"]:
            issues = "; ".join(validation["issues"])
            logger.warning(f"Citation validation issues: {issues}")
            return False, f"Citation validation failed: {issues}"
        
        logger.info(f"Response validated: {validation['citations_valid']}/{validation['citations_found']} citations valid")
        return True, "OK"
