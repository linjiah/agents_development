# Rate Limit & Quota Management Guide

## Understanding Rate Limits

The Gemini API free tier has **strict rate limits**:
- **20 requests per day per model** (for free tier)
- Models like `gemini-2.5-flash` may not be available on free tier
- Quota resets periodically (usually daily)

## What Was Fixed

### ✅ Automatic Retry Logic
- Automatically retries on rate limit errors (429)
- Extracts retry delay from error message
- Uses exponential backoff (5s, 15s, 30s)
- Maximum 3 retry attempts

### ✅ Better Error Messages
- Clear explanation of rate limit issues
- Helpful links to usage dashboard
- Suggestions for resolving the issue

### ✅ Model Fallback
- Defaults to `gemini-1.5-flash` (best free tier option)
- Automatically tries other free tier models if one fails
- Avoids paid-tier models that may not be available

## Recommended Models for Free Tier

| Model | Free Tier | Requests/Day | Best For |
|-------|-----------|--------------|----------|
| `gemini-1.5-flash` | ✅ Yes | 20 | **Recommended** - Fast, reliable |
| `gemini-1.5-pro` | ✅ Yes | Limited | Better quality, slower |
| `gemini-pro` | ✅ Yes | Limited | Older, stable |
| `gemini-2.5-flash` | ❌ No | N/A | Paid tier only |
| `gemini-2.0-flash-exp` | ❌ No | N/A | Experimental, paid |

## How to Fix Rate Limit Issues

### Option 1: Wait and Retry (Automatic)
The agent now automatically:
- Detects rate limit errors
- Waits the suggested time (from error message)
- Retries up to 3 times
- Shows progress in logs

### Option 2: Use Free Tier Model
Set in your `.env` file:
```bash
GEMINI_MODEL=gemini-1.5-flash
```

### Option 3: Check Your Usage
Visit: https://ai.dev/usage?tab=rate-limit
- See current usage
- Check when quota resets
- Monitor rate limits

### Option 4: Upgrade Plan (If Needed)
If you need more requests:
1. Go to Google Cloud Console
2. Upgrade your billing plan
3. Higher quotas available

## Current Implementation

The agent now:
- ✅ Automatically retries on rate limits
- ✅ Uses free tier models by default
- ✅ Provides helpful error messages
- ✅ Extracts retry delay from errors
- ✅ Falls back to other models if needed

## Tips

1. **Use `gemini-1.5-flash`** - Best free tier option
2. **Monitor usage** - Check dashboard regularly
3. **Wait between requests** - Don't spam the API
4. **Use caching** - Reuse responses when possible
5. **Batch requests** - Combine multiple queries when possible

---

**The agent will now automatically handle rate limits!** ⚡

