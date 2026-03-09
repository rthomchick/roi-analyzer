import anthropic
import time
import json
import re
import logging
from typing import Any, Callable, Dict, Optional, List
from datetime import datetime
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =====================================================
# PATTERN 1: RETRYABLE API CALLS
# =====================================================

class RetryableAPICall:
    """
    Handles transient failures with exponential backoff
    
    Use for: API timeouts, network errors, rate limits
    """
    
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0):
        """
        Args:
            max_retries: Maximum retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            Exception if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{self.max_retries}")
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"✅ Success after {attempt + 1} attempts")
                
                return result
                
            except anthropic.APITimeoutError as e:
                last_exception = e
                logger.warning(f"⏱️  Timeout on attempt {attempt + 1}: {e}")
                
            except anthropic.RateLimitError as e:
                last_exception = e
                logger.warning(f"🚦 Rate limit on attempt {attempt + 1}: {e}")
                
                # Check for Retry-After header
                retry_after = getattr(e, 'retry_after', None)
                if retry_after:
                    wait_time = float(retry_after)
                    logger.info(f"   Server requested {wait_time}s wait")
                else:
                    wait_time = self._calculate_backoff(attempt)
                    
            except anthropic.APIConnectionError as e:
                last_exception = e
                logger.warning(f"🌐 Connection error on attempt {attempt + 1}: {e}")
                wait_time = self._calculate_backoff(attempt)
                
            except anthropic.APIError as e:
                # Some API errors are retryable, others aren't
                if self._is_retryable_api_error(e):
                    last_exception = e
                    logger.warning(f"⚠️  Retryable API error on attempt {attempt + 1}: {e}")
                    wait_time = self._calculate_backoff(attempt)
                else:
                    # Non-retryable API error, fail immediately
                    logger.error(f"❌ Non-retryable API error: {e}")
                    raise
            
            # Wait before retry (unless this was the last attempt)
            if attempt < self.max_retries - 1:
                logger.info(f"   Waiting {wait_time:.1f}s before retry...")
                time.sleep(wait_time)
        
        # All retries exhausted
        logger.error(f"❌ All {self.max_retries} retries exhausted")
        raise Exception(f"Max retries exceeded. Last error: {last_exception}")
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter"""
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        # Add jitter (±20%) to prevent thundering herd
        jitter = delay * 0.2 * (2 * time.time() % 1 - 0.5)
        return delay + jitter
    
    def _is_retryable_api_error(self, error: anthropic.APIError) -> bool:
        """Determine if an API error is worth retrying"""
        # 5xx errors are typically transient server issues
        if hasattr(error, 'status_code'):
            return 500 <= error.status_code < 600
        return False


# =====================================================
# PATTERN 2: DEFENSIVE PARSER
# =====================================================

class DefensiveParser:
    """
    Handles format mismatches with multiple parsing strategies
    
    Use for: LLM outputs that might be JSON, markdown, or plain text
    """
    
    @staticmethod
    def parse_json(text: str, fallback_to_text: bool = True) -> Dict[str, Any]:
        """
        Parse JSON with multiple fallback strategies
        
        Args:
            text: Text that might contain JSON
            fallback_to_text: If True, return raw text on parse failure
            
        Returns:
            Parsed JSON or fallback structure
        """
        # Strategy 1: Direct JSON parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract from markdown code block
        try:
            json_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Strategy 3: Extract from any code block
        try:
            code_match = re.search(r'```\s*\n(.*?)\n```', text, re.DOTALL)
            if code_match:
                return json.loads(code_match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Strategy 4: Find JSON-like structure anywhere in text
        try:
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, text, re.DOTALL)
            if matches:
                # Try each match
                for match in matches:
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        # All parsing strategies failed
        if fallback_to_text:
            logger.warning("⚠️  Could not parse as JSON, returning raw text")
            return {
                "status": "unparsed",
                "format": "text",
                "content": text,
                "warning": "Failed to parse as JSON"
            }
        else:
            raise ValueError(f"Could not parse as JSON: {text[:100]}...")
    
    @staticmethod
    def parse_number(text: str) -> Optional[float]:
        """
        Extract a number from text with fallbacks
        
        Args:
            text: Text that might contain a number
            
        Returns:
            Extracted number or None
        """
        # Strategy 1: Direct float conversion
        try:
            return float(text.strip())
        except ValueError:
            pass
        
        # Strategy 2: Extract first number from text
        try:
            numbers = re.findall(r'[-+]?\d*\.?\d+', text)
            if numbers:
                return float(numbers[0])
        except (ValueError, IndexError):
            pass
        
        logger.warning(f"⚠️  Could not extract number from: {text[:50]}")
        return None
    
    @staticmethod
    def parse_list(text: str, delimiter: str = '\n') -> List[str]:
        """
        Parse a list from text with multiple strategies
        
        Args:
            text: Text that might contain a list
            delimiter: Expected delimiter
            
        Returns:
            List of items
        """
        # Strategy 1: JSON array
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
        except:
            pass
        
        # Strategy 2: Delimited text
        items = text.split(delimiter)
        
        # Clean up items (remove numbering, bullets, etc.)
        cleaned = []
        for item in items:
            # Remove common list markers
            clean = re.sub(r'^\s*[-*•]\s*', '', item)  # Bullets
            clean = re.sub(r'^\s*\d+[\.)]\s*', '', clean)  # Numbering
            clean = clean.strip()
            
            if clean:
                cleaned.append(clean)
        
        return cleaned if cleaned else [text]


# =====================================================
# PATTERN 3: BUDGET MONITOR
# =====================================================

class BudgetMonitor:
    """
    Tracks resource usage and enables graceful degradation
    
    Use for: Token budgets, API quotas, memory limits
    """
    
    def __init__(self, 
                 budget_limit: int,
                 warning_threshold: float = 0.8,
                 critical_threshold: float = 0.95):
        """
        Args:
            budget_limit: Maximum tokens/quota
            warning_threshold: Warn when usage exceeds this fraction
            critical_threshold: Enter degraded mode at this fraction
        """
        self.budget_limit = budget_limit
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.usage = 0
        self.operations = []
    
    def check_available(self, required: int) -> Dict[str, Any]:
        """
        Check if budget available for operation
        
        Args:
            required: Tokens/quota required
            
        Returns:
            Status dict with recommendation
        """
        available = self.budget_limit - self.usage
        usage_pct = self.usage / self.budget_limit
        
        status = {
            "available": available,
            "required": required,
            "sufficient": available >= required,
            "usage_pct": usage_pct,
            "remaining_pct": 1 - usage_pct
        }
        
        # Determine mode
        if usage_pct >= self.critical_threshold:
            status["mode"] = "critical"
            status["recommendation"] = "skip_non_critical"
            logger.warning(f"🔴 CRITICAL: {usage_pct:.1%} budget used")
            
        elif usage_pct >= self.warning_threshold:
            status["mode"] = "warning"
            status["recommendation"] = "use_cheaper_alternatives"
            logger.warning(f"🟡 WARNING: {usage_pct:.1%} budget used")
            
        else:
            status["mode"] = "normal"
            status["recommendation"] = "proceed"
        
        return status
    
    def consume(self, amount: int, operation: str = "unknown"):
        """
        Record resource consumption
        
        Args:
            amount: Tokens/quota consumed
            operation: Description of operation
        """
        self.usage += amount
        self.operations.append({
            "operation": operation,
            "amount": amount,
            "timestamp": datetime.now().isoformat(),
            "total_after": self.usage
        })
        
        logger.info(f"💰 Consumed {amount:,} tokens ({operation})")
        logger.info(f"   Total: {self.usage:,} / {self.budget_limit:,} ({self.usage/self.budget_limit:.1%})")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get budget usage summary"""
        return {
            "budget_limit": self.budget_limit,
            "usage": self.usage,
            "remaining": self.budget_limit - self.usage,
            "usage_pct": self.usage / self.budget_limit,
            "operations_count": len(self.operations),
            "operations": self.operations
        }


# =====================================================
# PATTERN 4: VALIDATION LAYER
# =====================================================

class ValidationLayer:
    """
    Validates inputs before expensive operations
    
    Use for: User inputs, tool parameters, configuration
    """
    
    @staticmethod
    def validate_investment_params(investment: float, 
                                   conversion_lift: float) -> Dict[str, Any]:
        """
        Validate ROI analysis parameters
        
        Returns:
            Validation result with errors if any
        """
        errors = []
        warnings = []
        
        # Check investment amount
        if investment <= 0:
            errors.append("Investment must be positive")
        elif investment > 10_000_000:
            warnings.append(f"Investment of ${investment:,.0f} is very high")
        
        # Check conversion lift
        if conversion_lift <= 0:
            errors.append("Conversion lift must be positive")
        elif conversion_lift > 0.1:  # >10 percentage points
            errors.append("Conversion lift >10% is unrealistic")
        elif conversion_lift > 0.05:  # >5 percentage points
            warnings.append(f"Conversion lift of {conversion_lift:.1%} is aggressive")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @staticmethod
    def validate_math_expression(expression: str) -> Dict[str, Any]:
        """
        Validate mathematical expression for safety
        
        Returns:
            Validation result
        """
        errors = []
        
        # Only allow safe characters
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expression):
            invalid = set(expression) - allowed
            errors.append(f"Invalid characters: {invalid}")
        
        # Check for dangerous patterns
        dangerous = ["__", "import", "exec", "eval", "open", "file"]
        for pattern in dangerous:
            if pattern in expression.lower():
                errors.append(f"Dangerous pattern detected: {pattern}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "expression": expression
        }
    
    @staticmethod
    def validate_required_fields(data: Dict, required: List[str]) -> Dict[str, Any]:
        """
        Validate that required fields are present
        
        Args:
            data: Data dict to validate
            required: List of required field names
            
        Returns:
            Validation result
        """
        missing = [field for field in required if field not in data]
        
        return {
            "valid": len(missing) == 0,
            "missing": missing,
            "message": f"Missing required fields: {missing}" if missing else "All required fields present"
        }


# =====================================================
# PATTERN 5: ERROR LOGGER
# =====================================================

class ErrorLogger:
    """
    Comprehensive error logging and alerting
    
    Use for: Catastrophic errors that need human attention
    """
    
    def __init__(self, log_file: str = "errors.log"):
        """
        Args:
            log_file: Path to error log file
        """
        self.log_file = log_file
        
        # Setup file logging
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    def log_error(self, 
                  error: Exception,
                  context: Dict[str, Any],
                  severity: str = "error") -> str:
        """
        Log error with full context
        
        Args:
            error: The exception that occurred
            context: Contextual information
            severity: "warning", "error", or "critical"
            
        Returns:
            Error ID for user reference
        """
        error_id = self._generate_error_id()
        
        error_data = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        # Log to file
        if severity == "critical":
            logger.critical(f"🔥 CRITICAL ERROR [{error_id}]: {error}")
        else:
            logger.error(f"❌ ERROR [{error_id}]: {error}")
        
        logger.error(f"Context: {json.dumps(context, indent=2)}")
        logger.error(f"Traceback:\n{error_data['traceback']}")
        
        # In production, you'd also:
        # - Send to error tracking service (Sentry, Rollbar)
        # - Alert on-call engineer
        # - Update status page
        
        return error_id
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        import hashlib
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def get_user_friendly_message(self, error_id: str) -> str:
        """
        Generate user-friendly error message
        
        Args:
            error_id: Error ID from log_error
            
        Returns:
            Message suitable for end users
        """
        return f"""We encountered an unexpected error while processing your request.

Our team has been automatically notified and is investigating.

Error Reference: {error_id}

Please try again in a few minutes. If the problem persists, 
contact support with the error reference above."""


# =====================================================
# DEMO: ALL PATTERNS TOGETHER
# =====================================================

def demo_resilience_patterns():
    """Demonstrate all resilience patterns"""
    
    print("\n" + "🛡️ " * 20)
    print("RESILIENCE PATTERNS DEMO")
    print("🛡️ " * 20)
    
    # Pattern 1: Retry
    print("\n" + "="*70)
    print("PATTERN 1: Retryable API Call")
    print("="*70)
    
    retry = RetryableAPICall(max_retries=3, base_delay=1.0)
    
    def flaky_function(fail_count=[0]):
        """Simulates a function that fails first 2 times"""
        fail_count[0] += 1
        if fail_count[0] < 3:
            raise anthropic.APIConnectionError("Simulated connection error")
        return "Success!"
    
    try:
        result = retry.execute(flaky_function)
        print(f"\n✅ Final result: {result}")
    except Exception as e:
        print(f"\n❌ Failed: {e}")
    
    # Pattern 2: Defensive Parser
    print("\n" + "="*70)
    print("PATTERN 2: Defensive Parser")
    print("="*70)
    
    parser = DefensiveParser()
    
    test_inputs = [
        '{"name": "test", "value": 42}',  # Clean JSON
        '```json\n{"name": "test"}\n```',  # Markdown JSON
        'The result is {"name": "test"} as shown',  # Embedded JSON
        'Just plain text, no JSON here',  # No JSON
        '0.85',  # Number
        'The confidence is 0.85 or 85%'  # Number in text
    ]
    
    for inp in test_inputs:
        print(f"\nInput: {inp[:50]}")
        parsed = parser.parse_json(inp)
        print(f"Parsed: {parsed}")
    
    # Pattern 3: Budget Monitor
    print("\n" + "="*70)
    print("PATTERN 3: Budget Monitor")
    print("="*70)
    
    budget = BudgetMonitor(budget_limit=10000, warning_threshold=0.7)
    
    operations = [
        ("Initial query", 2000),
        ("Research", 3000),
        ("Analysis", 2500),
        ("Synthesis", 3000)  # This pushes over warning threshold
    ]
    
    for op_name, tokens in operations:
        status = budget.check_available(tokens)
        print(f"\n{op_name}: {tokens} tokens")
        print(f"   Status: {status['mode']}")
        print(f"   Recommendation: {status['recommendation']}")
        
        if status['sufficient']:
            budget.consume(tokens, op_name)
        else:
            print(f"   ⚠️  Insufficient budget, skipping")
    
    # Pattern 4: Validation
    print("\n" + "="*70)
    print("PATTERN 4: Validation Layer")
    print("="*70)
    
    validator = ValidationLayer()
    
    test_cases = [
        (500000, 0.006, "Valid input"),
        (-100000, 0.02, "Negative investment"),
        (1000000, 0.15, "Unrealistic lift"),
    ]
    
    for investment, lift, description in test_cases:
        print(f"\n{description}:")
        print(f"  Investment: ${investment:,.0f}")
        print(f"  Lift: {lift:.1%}")
        
        result = validator.validate_investment_params(investment, lift)
        print(f"  Valid: {result['valid']}")
        if result['errors']:
            print(f"  Errors: {result['errors']}")
        if result['warnings']:
            print(f"  Warnings: {result['warnings']}")
    
    # Pattern 5: Error Logger
    print("\n" + "="*70)
    print("PATTERN 5: Error Logger")
    print("="*70)
    
    error_logger = ErrorLogger()
    
    try:
        # Simulate an error
        raise ValueError("Something went wrong in production")
    except Exception as e:
        error_id = error_logger.log_error(
            error=e,
            context={
                "user_id": "user_123",
                "operation": "roi_analysis",
                "input_params": {"investment": 500000}
            },
            severity="error"
        )
        
        message = error_logger.get_user_friendly_message(error_id)
        print(f"\n{message}")
    
    print("\n" + "="*70)
    print("✅ ALL PATTERNS DEMONSTRATED")
    print("="*70)


if __name__ == "__main__":
    demo_resilience_patterns()