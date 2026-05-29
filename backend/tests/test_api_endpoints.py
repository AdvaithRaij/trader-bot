"""
Test Suite for API Endpoints

Tests all FastAPI endpoints with real data.

Run:
    pytest backend/tests/test_api_endpoints.py -v
    
Note: Requires the FastAPI server to be running on localhost:8001
"""

import pytest
import httpx
from loguru import logger
from conftest import assert_real_price, assert_no_mock_data


BASE_URL = "http://localhost:8001"


class TestAPIEndpoints:
    """Test FastAPI endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint."""
        logger.info("Testing health check endpoint...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        
        logger.success("✅ Health check passed")

    @pytest.mark.asyncio
    async def test_stock_search_endpoint(self):
        """Test stock search endpoint with NIFTY 200 data."""
        logger.info("Testing stock search endpoint...")
        
        async with httpx.AsyncClient() as client:
            # Test search with query
            response = await client.get(f"{BASE_URL}/api/stocks/search?query=RELIANCE")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "stocks" in data
            assert len(data["stocks"]) > 0
            
            # Verify RELIANCE is in results
            symbols = [s["symbol"] for s in data["stocks"]]
            assert "RELIANCE" in symbols
            
            # Verify no mock data
            assert_no_mock_data(data, "stock search")
        
        logger.success(f"✅ Stock search returned {len(data['stocks'])} results")

    @pytest.mark.asyncio
    async def test_stock_quote_endpoint(self):
        """Test stock quote endpoint with real data."""
        logger.info("Testing stock quote endpoint...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/stocks/RELIANCE/quote")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "symbol" in data
            assert "price" in data
            assert data["symbol"] == "RELIANCE"
            
            # Verify real price
            assert_real_price(data["price"], "RELIANCE")
            
            # Verify OHLCV data
            assert "open" in data
            assert "high" in data
            assert "low" in data
            assert "volume" in data
            
            # Verify no mock data
            assert_no_mock_data(data, "stock quote")
        
        logger.success(f"✅ Stock quote: RELIANCE @ ₹{data['price']:.2f}")

    @pytest.mark.asyncio
    async def test_pipeline_screen_endpoint(self):
        """Test pipeline screening endpoint."""
        logger.info("Testing pipeline screening endpoint...")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{BASE_URL}/api/pipeline/screen")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "candidates" in data
            assert "market_context" in data
            assert len(data["candidates"]) > 0
            
            # Verify candidates have required fields
            for candidate in data["candidates"]:
                assert "symbol" in candidate
                assert "score" in candidate
                assert "liquidity" in candidate
                assert "technicals" in candidate
            
            # Verify no mock data
            assert_no_mock_data(data, "screening output")
        
        logger.success(f"✅ Screening returned {len(data['candidates'])} candidates")

    @pytest.mark.asyncio
    async def test_pipeline_analyze_multi_endpoint(self):
        """Test multi-strategy analysis endpoint."""
        logger.info("Testing multi-strategy analysis endpoint...")
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            # First, get candidates from screening
            screen_response = await client.post(f"{BASE_URL}/api/pipeline/screen")
            candidates = screen_response.json()["candidates"]
            
            if len(candidates) == 0:
                logger.warning("No candidates to analyze")
                return
            
            # Analyze top candidate
            symbols = [candidates[0]["symbol"]]
            
            response = await client.post(
                f"{BASE_URL}/api/pipeline/analyze-multi",
                json={"symbols": symbols}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "analyses" in data
            assert len(data["analyses"]) > 0
            
            # Verify analysis structure
            analysis = data["analyses"][0]
            assert "symbol" in analysis
            assert "fundamental" in analysis
            assert "news_based" in analysis
            assert "combined" in analysis
            assert "recommendation" in analysis
            
            # Verify no mock data
            assert_no_mock_data(data, "multi-strategy analysis")
        
        logger.success(f"✅ Multi-strategy analysis completed for {symbols[0]}")

