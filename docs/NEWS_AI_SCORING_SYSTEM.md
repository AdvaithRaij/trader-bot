# News AI Scoring & Analysis System

## Current Implementation

### 1. AI Analysis Process

Every news article goes through this pipeline:

```
News Article → AI Analysis → Scoring → Display
```

**Flow:**
1. **Fetch News** from 3 sources (Google News, Economic Times, MoneyControl)
2. **Deduplicate** based on title similarity
3. **AI Analysis** using Gemini 2.0 Flash for each article
4. **Cache Results** to avoid re-analyzing same news
5. **Return to Frontend** with scores and analysis

---

## AI Involvement (Current)

### What AI Does:

The AI (Gemini 2.0 Flash) analyzes each news article and provides:

#### 1. **Impact Score** (HIGH/MEDIUM/LOW)
- Assesses how much this news will move the market
- Based on:
  - Magnitude of the event (earnings, policy changes, etc.)
  - Affected companies/sectors
  - Market conditions
  - Historical patterns

**Examples:**
- `HIGH`: "RBI cuts interest rates by 50 basis points"
- `MEDIUM`: "TCS announces 10% dividend increase"
- `LOW`: "Minor regulatory filing by small-cap company"

#### 2. **Sentiment** (POSITIVE/NEGATIVE/NEUTRAL)
- Determines if news is bullish, bearish, or neutral
- Considers:
  - Direct impact on stock prices
  - Market psychology
  - Sector implications

**Examples:**
- `POSITIVE`: "Record quarterly profits", "New government contracts"
- `NEGATIVE`: "Earnings miss", "Regulatory probe"
- `NEUTRAL`: "Management change", "Stock split announcement"

#### 3. **Related Stocks** (Array of symbols)
- Identifies which stocks will be affected
- Includes:
  - Direct mentions (company names)
  - Sector implications (if banking news → HDFC, ICICI, etc.)
  - Index impact (NIFTY, BANKNIFTY)

**Examples:**
- "Reliance announces new venture" → `["RELIANCE", "NIFTY"]`
- "IT sector outlook positive" → `["TCS", "INFY", "WIPRO", "NIFTY"]`
- "Banking regulations tightened" → `["HDFC", "ICICI", "SBI", "BANKNIFTY"]`

#### 4. **Analysis** (2-3 sentence explanation)
- Human-readable explanation of the impact
- Explains WHY this news matters
- Connects news to trading implications

**Example:**
```
"This news indicates strong earnings momentum in the IT sector, 
which could drive NIFTY higher in the short term. TCS and Infosys 
are likely to see increased buying interest from institutional investors."
```

#### 5. **Timeframe** (IMMEDIATE/SHORT_TERM/LONG_TERM)
- When the impact will be felt
- Helps traders decide entry/exit timing

**Examples:**
- `IMMEDIATE`: Intraday impact (earnings announcements, policy decisions)
- `SHORT_TERM`: 1-5 days (sector trends, analyst upgrades)
- `LONG_TERM`: Weeks to months (structural reforms, new regulations)

---

## AI Prompt (Current)

Located in: `backend/prompts/news_analysis.txt`

```
Analyze this market news article and provide impact assessment:

Title: {title}
Summary: {summary}
Source: {source}

Provide a JSON response with:
1. "impact": overall market impact (HIGH/MEDIUM/LOW)
2. "sentiment": sentiment (POSITIVE/NEGATIVE/NEUTRAL)
3. "relatedStocks": array of stock symbols that could be affected
4. "analysis": 2-3 sentence analysis of how this news impacts the market/stocks
5. "timeframe": impact timeframe (IMMEDIATE/SHORT_TERM/LONG_TERM)

Focus on Indian market stocks (NIFTY, BANKNIFTY, major stocks like RELIANCE, TCS, INFY, HDFC, etc.)

Return ONLY valid JSON, no markdown formatting.
```

---

## Fallback: Mock Analysis

When AI is unavailable (quota exceeded, API down, or `MOCK_AI=true`), the system uses **keyword-based analysis**:

### Mock Analysis Logic:

```python
def mock_analysis(news_item):
    text = f"{title} {summary}".lower()
    
    # Impact scoring
    high_impact_keywords = ['crash', 'surge', 'record', 'historic', 'major', 'significant']
    impact = 'HIGH' if any(kw in text for kw in high_impact_keywords) else 'MEDIUM'
    
    # Sentiment scoring
    positive_keywords = ['surge', 'gain', 'profit', 'growth', 'positive', 'bullish', 'rally']
    negative_keywords = ['crash', 'fall', 'loss', 'decline', 'negative', 'bearish', 'drop']
    
    if any(kw in text for kw in positive_keywords):
        sentiment = 'POSITIVE'
    elif any(kw in text for kw in negative_keywords):
        sentiment = 'NEGATIVE'
    else:
        sentiment = 'NEUTRAL'
    
    # Stock detection
    stock_keywords = {
        'NIFTY': ['nifty', 'index', 'market'],
        'BANKNIFTY': ['bank', 'banking'],
        'RELIANCE': ['reliance', 'ril'],
        'TCS': ['tcs', 'tata consultancy'],
        'INFY': ['infosys', 'infy'],
        'HDFC': ['hdfc'],
        'ICICI': ['icici']
    }
    
    related_stocks = []
    for stock, keywords in stock_keywords.items():
        if any(kw in text for kw in keywords):
            related_stocks.append(stock)
    
    if not related_stocks:
        related_stocks = ['NIFTY']
    
    return {
        'impact': impact,
        'sentiment': sentiment,
        'relatedStocks': related_stocks,
        'analysis': f"This news may have {impact.lower()} impact on {', '.join(related_stocks[:3])} with {sentiment.lower()} sentiment.",
        'timeframe': 'SHORT_TERM'
    }
```

---

## Scoring System (Proposed Enhancements)

### Current Limitations:
1. ❌ No numerical confidence score (0-100)
2. ❌ No relevance score for intraday trading
3. ❌ No urgency/recency weighting
4. ❌ No source credibility scoring
5. ❌ No historical accuracy tracking

### Proposed Improvements:

#### 1. **Confidence Score** (0-100)
How confident is the AI in its analysis?

```json
{
  "confidence": 85,
  "reasoning": "Clear earnings data with historical context"
}
```

**Factors:**
- Clarity of news (earnings data = high, rumors = low)
- Source credibility (ET = high, unknown blog = low)
- Historical pattern match
- Data completeness

#### 2. **Intraday Relevance Score** (0-100)
How relevant is this news for TODAY's trading?

```json
{
  "intradayRelevance": 92,
  "reasoning": "Breaking news with immediate price impact expected"
}
```

**Factors:**
- Recency (last 1 hour = 100, yesterday = 20)
- Market hours (during trading = high, after close = medium)
- Event type (earnings = high, opinion piece = low)
- Volatility potential

#### 3. **Urgency Score** (0-100)
How quickly should a trader act on this?

```json
{
  "urgency": 95,
  "reasoning": "Market-moving announcement during trading hours"
}
```

**Factors:**
- Time sensitivity
- Price impact potential
- Liquidity considerations
- Market phase (opening = high, mid-day = medium)

#### 4. **Source Credibility Score** (0-100)
How trustworthy is the news source?

```json
{
  "sourceCredibility": 90,
  "source": "Economic Times",
  "reasoning": "Tier-1 financial news source with verified track record"
}
```

**Tiers:**
- **Tier 1 (90-100)**: Economic Times, Bloomberg, Reuters, Moneycontrol
- **Tier 2 (70-89)**: Business Standard, Mint, Financial Express
- **Tier 3 (50-69)**: Regional news, sector-specific publications
- **Tier 4 (0-49)**: Blogs, social media, unverified sources

#### 5. **Historical Accuracy Tracking**
Track how accurate past predictions were:

```json
{
  "historicalAccuracy": {
    "aiPredictionAccuracy": 78,
    "sampleSize": 150,
    "lastUpdated": "2025-11-12"
  }
}
```

**Metrics:**
- Did HIGH impact news actually move the market?
- Was sentiment prediction correct?
- Did related stocks actually get affected?

---

## Enhanced AI Prompt (Proposed)

```
Analyze this market news article for intraday trading:

Title: {title}
Summary: {summary}
Source: {source}
Published: {publishedAt}
Current Time: {currentTime}

Provide a comprehensive JSON response with:

1. "impact": overall market impact (HIGH/MEDIUM/LOW)
2. "sentiment": sentiment (POSITIVE/NEGATIVE/NEUTRAL)
3. "relatedStocks": array of stock symbols that could be affected
4. "analysis": 2-3 sentence analysis of trading implications
5. "timeframe": impact timeframe (IMMEDIATE/SHORT_TERM/LONG_TERM)

6. "confidence": confidence in this analysis (0-100)
   - Consider: data clarity, source credibility, historical patterns
   
7. "intradayRelevance": relevance for TODAY's trading (0-100)
   - Consider: recency, market hours, event type, volatility potential
   
8. "urgency": how quickly traders should act (0-100)
   - Consider: time sensitivity, price impact, market phase
   
9. "tradingImplications": {
     "entrySignal": "BUY/SELL/HOLD",
     "targetStocks": ["STOCK1", "STOCK2"],
     "expectedMove": "percentage or points",
     "riskLevel": "HIGH/MEDIUM/LOW"
   }

10. "reasoning": detailed explanation of scores and recommendations

Focus on Indian market (NIFTY, BANKNIFTY, major stocks).
Return ONLY valid JSON, no markdown.
```

---

## Implementation Roadmap

### Phase 1: Enhanced Scoring (Week 1)
- [ ] Add confidence score to AI prompt
- [ ] Add intraday relevance score
- [ ] Add urgency score
- [ ] Update frontend to display scores

### Phase 2: Source Credibility (Week 2)
- [ ] Create source credibility database
- [ ] Implement source scoring
- [ ] Weight AI analysis by source credibility
- [ ] Add source badges in UI

### Phase 3: Historical Tracking (Week 3)
- [ ] Store AI predictions in database
- [ ] Track actual market movements
- [ ] Calculate prediction accuracy
- [ ] Display accuracy metrics in UI

### Phase 4: Trading Signals (Week 4)
- [ ] Add trading implications to AI analysis
- [ ] Generate entry/exit signals
- [ ] Calculate expected price moves
- [ ] Integrate with trading strategy

---

## Current vs. Proposed Comparison

| Feature | Current | Proposed |
|---------|---------|----------|
| Impact Assessment | ✅ HIGH/MEDIUM/LOW | ✅ Same + numerical score |
| Sentiment | ✅ POSITIVE/NEGATIVE/NEUTRAL | ✅ Same + strength (0-100) |
| Related Stocks | ✅ Array of symbols | ✅ Same + impact % per stock |
| Analysis | ✅ 2-3 sentences | ✅ Same + detailed reasoning |
| Timeframe | ✅ IMMEDIATE/SHORT/LONG | ✅ Same + specific hours/days |
| Confidence | ❌ Not available | ✅ 0-100 score |
| Intraday Relevance | ❌ Not available | ✅ 0-100 score |
| Urgency | ❌ Not available | ✅ 0-100 score |
| Source Credibility | ❌ Not tracked | ✅ 0-100 score |
| Trading Signals | ❌ Not available | ✅ BUY/SELL/HOLD |
| Historical Accuracy | ❌ Not tracked | ✅ Tracked & displayed |

---

## Summary

**Current AI Involvement:**
- ✅ Analyzes every news article
- ✅ Provides impact, sentiment, stocks, analysis, timeframe
- ✅ Caches results to save API quota
- ✅ Falls back to keyword-based analysis when AI unavailable

**What's Missing:**
- ❌ Numerical confidence/relevance scores
- ❌ Trading signals (BUY/SELL/HOLD)
- ❌ Source credibility weighting
- ❌ Historical accuracy tracking
- ❌ Intraday-specific scoring

**Next Steps:**
1. Enhance AI prompt with numerical scores
2. Add trading signal generation
3. Implement source credibility system
4. Track prediction accuracy over time

