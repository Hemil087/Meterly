-- KEYS[1]: rate limit key  e.g. "rl:subscription_id"
-- ARGV[1]: requests  (tokens per window)
-- ARGV[2]: window_seconds
-- ARGV[3]: burst  (max bucket size; 0 = use requests)
-- ARGV[4]: now_ms (unix timestamp in milliseconds)

local key            = KEYS[1]
local requests       = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])
local burst          = tonumber(ARGV[3])
local now            = tonumber(ARGV[4])

if burst == 0 then burst = requests end

-- Refill rate: tokens added per millisecond
local rate = requests / (window_seconds * 1000)

local data       = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens     = tonumber(data[1])
local last_refill = tonumber(data[2])

if tokens == nil then
    -- First ever request: full bucket, consume one
    tokens = burst - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('PEXPIRE', key, window_seconds * 2000)
    return {1, tokens, 0}
end

-- Refill bucket based on elapsed time
local elapsed = now - last_refill
tokens = math.min(burst, tokens + math.floor(elapsed * rate))

if tokens >= 1 then
    tokens = tokens - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('PEXPIRE', key, window_seconds * 2000)
    return {1, tokens, 0}                          -- allowed
else
    local retry_after_ms = math.ceil((1 - tokens) / rate)
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('PEXPIRE', key, window_seconds * 2000)
    return {0, 0, retry_after_ms}                  -- denied
end