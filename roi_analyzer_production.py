import anthropic
import os
from dotenv import load_dotenv
from tool_library import ToolLibrary
from datetime import datetime
import json

from resilience import (
    RetryableAPICall,
    DefensiveParser,
    BudgetMonitor,
    ValidationLayer,
    ErrorLogger
)

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


class ProductionROIAnalyzer:
    """
    Production-ready ROI analyzer with full resilience
    
    Resilience features:
    - ✅ Input validation before expensive operations
    - ✅ Retry logic for transient failures
    - ✅ Defensive parsing of LLM outputs
    - ✅ Budget monitoring and graceful degradation
    - ✅ Comprehensive error logging
    - ✅ Partial result recovery
    - ✅ Realistic conversion economics
    - ✅ Assumption validation with executive scrutiny flags
    """
    
    def __init__(self, 
                 annual_traffic: int = 1000000,
                 token_budget: int = 30000):
        """
        Initialize production analyzer
        
        Args:
            annual_traffic: Annual site traffic
            token_budget: Maximum tokens for entire analysis
        """
        self.tools = ToolLibrary()
        self.tool_schemas = self.tools.get_all_tools()
        self.annual_traffic = annual_traffic
        
        # Resilience components
        self.retry = RetryableAPICall(max_retries=3, base_delay=2.0)
        self.parser = DefensiveParser()
        self.budget = BudgetMonitor(
            budget_limit=token_budget,
            warning_threshold=0.7,
            critical_threshold=0.9
        )
        self.validator = ValidationLayer()
        self.error_logger = ErrorLogger(log_file="roi_analyzer_errors.log")
        
        # Tracking
        self.analysis_data = {}
        self.tool_calls = []
        self.partial_results = {}
        
        print("📊 Production ROI Analyzer initialized")
        print(f"   Annual traffic: {annual_traffic:,} visitors")
        print(f"   Token budget: {token_budget:,}")
        print(f"   Resilience: ENABLED ✅")
    
    def analyze(self, 
                investment_amount: float,
                expected_conversion_lift: float,
                scenario_description: str = None) -> dict:
        """
        Analyze ROI with full resilience
        
        Returns:
            Analysis results or error details
        """
        print("\n" + "="*70)
        print("PRODUCTION ROI ANALYSIS")
        print("="*70)
        
        try:
            # STEP 0: Validate inputs (Pattern 4)
            validation_result = self._validate_inputs(
                investment_amount,
                expected_conversion_lift
            )
            
            if not validation_result['valid']:
                return {
                    "status": "validation_failed",
                    "errors": validation_result['errors'],
                    "warnings": validation_result['warnings'],
                    "timestamp": datetime.now().isoformat()
                }
            
            # Store validated inputs
            self.analysis_data = {
                "investment": investment_amount,
                "expected_lift": expected_conversion_lift,
                "scenario": scenario_description,
                "timestamp": datetime.now().isoformat()
            }
            
            # Show warnings if any
            if validation_result['warnings']:
                print(f"\n⚠️  Input Warnings:")
                for warning in validation_result['warnings']:
                    print(f"   - {warning}")
            
            # STEP 1: Gather data
            print("\n--- STEP 1: Gathering Platform Data ---")
            try:
                current_data = self._gather_current_data_resilient()
                self.partial_results['current_data'] = current_data
            except Exception as e:
                return self._handle_step_failure("gather_data", e)
            
            # STEP 2: Calculate impact
            print("\n--- STEP 2: Calculating Financial Impact ---")
            try:
                financial_impact = self._calculate_impact_resilient(
                    current_data["revenue"],
                    current_data["conversion_rate"],
                    expected_conversion_lift
                )
                self.partial_results['financial_impact'] = financial_impact
            except Exception as e:
                return self._handle_step_failure("calculate_impact", e)
            
            # STEP 3: Validate assumptions
            print("\n--- STEP 3: Validating Assumptions ---")
            try:
                validation = self._validate_assumptions(
                    investment_amount,
                    expected_conversion_lift,
                    financial_impact
                )
                self.partial_results['validation'] = validation
            except Exception as e:
                return self._handle_step_failure("validate_assumptions", e)
            
            # STEP 4: Research benchmarks (optional if budget critical)
            print("\n--- STEP 4: Researching Benchmarks ---")
            budget_status = self.budget.check_available(1000)  # Estimate
            
            if budget_status['mode'] == 'critical':
                print("⚠️  Budget critical, skipping benchmark research")
                benchmarks = {"sources": [], "skipped": True}
            else:
                try:
                    benchmarks = self._research_benchmarks_resilient(expected_conversion_lift)
                    self.partial_results['benchmarks'] = benchmarks
                except Exception as e:
                    print(f"⚠️  Benchmark research failed: {e}")
                    benchmarks = {"sources": [], "error": str(e)}
            
            # STEP 5: Generate recommendation
            print("\n--- STEP 5: Generating Recommendation ---")
            budget_status = self.budget.check_available(2000)  # Estimate
            
            if budget_status['mode'] == 'critical':
                print("⚠️  Budget critical, using simplified recommendation")
                recommendation = self._generate_simple_recommendation(
                    investment_amount,
                    financial_impact,
                    validation
                )
            else:
                try:
                    recommendation = self._generate_recommendation_resilient(
                        investment_amount,
                        expected_conversion_lift,
                        current_data,
                        financial_impact,
                        validation,
                        benchmarks
                    )
                except Exception as e:
                    print(f"⚠️  Full recommendation failed, using fallback: {e}")
                    recommendation = self._generate_simple_recommendation(
                        investment_amount,
                        financial_impact,
                        validation
                    )
            
            # Compile results
            results = {
                "status": "success",
                "investment": investment_amount,
                "expected_lift": expected_conversion_lift,
                "current_data": current_data,
                "financial_impact": financial_impact,
                "validation": validation,
                "benchmarks": benchmarks,
                "recommendation": recommendation,
                "metadata": {
                    "budget_summary": self.budget.get_summary(),
                    "tool_calls": len(self.tool_calls),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            self.analysis_data.update(results)
            
            print("\n✅ Analysis complete")
            print(f"💰 Budget used: {self.budget.usage:,} / {self.budget.budget_limit:,}")
            
            return results
            
        except Exception as e:
            # Catastrophic failure (Pattern 5)
            error_id = self.error_logger.log_error(
                error=e,
                context={
                    "investment": investment_amount,
                    "lift": expected_conversion_lift,
                    "partial_results": list(self.partial_results.keys()),
                    "budget_used": self.budget.usage
                },
                severity="critical"
            )
            
            return {
                "status": "partial_failure",
                "error_id": error_id,
                "partial_results": self.partial_results,
                "message": f"Analysis failed. Error ID: {error_id}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _validate_inputs(self, investment: float, lift: float) -> dict:
        """Validate inputs before starting analysis (Pattern 4)"""
        print(f"\n🔍 Validating inputs...")
        print(f"   Investment: ${investment:,.0f}")
        print(f"   Expected lift: {lift:.1%}")
        
        result = self.validator.validate_investment_params(investment, lift)
        
        if result['valid']:
            print(f"   ✅ Inputs valid")
        else:
            print(f"   ❌ Validation failed:")
            for error in result['errors']:
                print(f"      - {error}")
        
        return result
    
    def _gather_current_data_resilient(self) -> dict:
        """Gather data with retry logic (Pattern 1)"""
        
        def safe_lookup(entity_type: str, entity_id: str = None):
            """Wrapper for tool lookup with validation"""
            result = self.tools.servicenow_lookup(entity_type, entity_id)
            
            if not result.get('success'):
                raise ValueError(f"Lookup failed: {result.get('error')}")
            
            return result
        
        # Get revenue with retry
        print("📊 Looking up revenue...")
        revenue_result = self.retry.execute(safe_lookup, "metric", "revenue")
        revenue = revenue_result.get("value", 0)
        print(f"   ${revenue:,.0f}")
        
        # Get conversion rate with retry
        print("📊 Looking up conversion rate...")
        conversion_result = self.retry.execute(safe_lookup, "metric", "conversion_rate")
        conversion_rate = conversion_result.get("value", 0)
        print(f"   {conversion_rate:.2%}")
        
        # Get uptime (with graceful degradation if fails)
        print("📊 Looking up platform uptime...")
        try:
            uptime_result = self.retry.execute(safe_lookup, "metric", "platform_uptime")
            uptime = uptime_result.get("value", 0)
            print(f"   {uptime:.2%}")
        except Exception as e:
            print(f"   ⚠️  Failed to get uptime: {e}, using default")
            uptime = 0.99  # Default fallback
        
        # Get personalization engine data
        print("📊 Looking up personalization engine...")
        pe_result = self.retry.execute(safe_lookup, "feature", "personalization_engine")
        pe_data = pe_result.get("data", {})
        print(f"   Adoption: {pe_data.get('adoption_rate', 0):.1%}")
        
        return {
            "revenue": revenue,
            "conversion_rate": conversion_rate,
            "uptime": uptime,
            "personalization_engine": pe_data
        }
    
    def _calculate_impact_resilient(self, 
                                   current_revenue: float,
                                   current_conversion: float,
                                   lift: float) -> dict:
        """Calculate impact with defensive parsing (Pattern 2)"""
        
        def safe_calculate(expression: str) -> float:
            """Wrapper for calculation with validation and parsing"""
            # Validate expression (Pattern 4)
            validation = self.validator.validate_math_expression(expression)
            if not validation['valid']:
                raise ValueError(f"Invalid expression: {validation['errors']}")
            
            # Execute calculation
            result = self.tools.calculate(expression)
            
            if not result.get('success'):
                raise ValueError(f"Calculation failed: {result.get('error')}")
            
            # Parse result defensively (Pattern 2)
            value = result.get('result')
            if value is None:
                # Try parsing from formatted string
                value = self.parser.parse_number(result.get('formatted', '0'))
            
            return value
        
        annual_traffic = self.annual_traffic
        
        print(f"🧮 Calculating impact...")
        
        # Calculate with retry
        current_transactions = self.retry.execute(
            safe_calculate,
            f"{annual_traffic} * {current_conversion}"
        )
        
        average_order_value = self.retry.execute(
            safe_calculate,
            f"{current_revenue} / {current_transactions}"
        )
        
        new_conversion = self.retry.execute(
            safe_calculate,
            f"{current_conversion} + {lift}"
        )
        
        new_transactions = self.retry.execute(
            safe_calculate,
            f"{annual_traffic} * {new_conversion}"
        )
        
        additional_transactions = self.retry.execute(
            safe_calculate,
            f"{new_transactions} - {current_transactions}"
        )
        
        additional_revenue = self.retry.execute(
            safe_calculate,
            f"{additional_transactions} * {average_order_value}"
        )
        
        relative_lift = self.retry.execute(
            safe_calculate,
            f"({new_conversion} / {current_conversion} - 1)"
        )
        
        new_revenue = self.retry.execute(
            safe_calculate,
            f"{current_revenue} + {additional_revenue}"
        )
        
        print(f"   Additional revenue: ${additional_revenue:,.0f}")
        print(f"   Relative lift: {relative_lift:.1%}")
        
        # Consume budget for this step
        self.budget.consume(500, "calculate_impact")
        
        return {
            "additional_revenue": additional_revenue,
            "new_revenue": new_revenue,
            "new_conversion_rate": new_conversion,
            "relative_lift": relative_lift,
            "additional_transactions": additional_transactions,
            "new_transactions": new_transactions,
            "current_transactions": current_transactions,
            "average_order_value": average_order_value,
            "annual_traffic": annual_traffic
        }
    
    def _validate_assumptions(self,
                             investment: float,
                             expected_lift: float,
                             financial_impact: dict) -> dict:
        """Validate assumptions (reusing logic from original)"""
        
        print(f"\n🔍 Validating assumptions...")
        
        warnings = []
        
        simple_roi = (financial_impact['additional_revenue'] / investment - 1)
        
        if simple_roi > 2.0:
            warnings.append({
                "type": "unrealistic_roi",
                "message": f"ROI of {simple_roi*100:.0f}% is exceptionally high",
                "severity": "high"
            })
        elif simple_roi < 0.2:
            warnings.append({
                "type": "low_roi",
                "message": f"ROI of {simple_roi*100:.0f}% is below typical hurdle rates (20-30%)",
                "severity": "medium"
            })
        
        relative_lift = financial_impact.get('relative_lift', 0)
        
        if relative_lift > 0.5:
            warnings.append({
                "type": "aggressive_conversion_target",
                "message": f"{relative_lift*100:.0f}% relative improvement is very aggressive",
                "severity": "high"
            })
        elif relative_lift > 0.3:
            warnings.append({
                "type": "optimistic_conversion_target",
                "message": f"{relative_lift*100:.0f}% relative improvement is optimistic",
                "severity": "medium"
            })
        
        payback_period = investment / financial_impact.get('additional_revenue', 1)
        
        if payback_period > 2.0:
            warnings.append({
                "type": "long_payback",
                "message": f"Payback period of {payback_period:.1f} years exceeds typical 12-18 month targets",
                "severity": "medium"
            })
        elif payback_period < 0.5:
            warnings.append({
                "type": "fast_payback",
                "message": f"Payback period of {payback_period:.1f} years ({payback_period*12:.0f} months) is unusually fast",
                "severity": "low"
            })
        
        current_conversion = financial_impact.get('new_conversion_rate', 0) - expected_lift
        
        if current_conversion < 0.02:
            warnings.append({
                "type": "low_baseline",
                "message": f"Current conversion rate of {current_conversion:.1%} is below industry average (2-4%)",
                "severity": "info"
            })
        elif current_conversion > 0.06:
            warnings.append({
                "type": "high_baseline",
                "message": f"Current conversion rate of {current_conversion:.1%} is above industry average (2-4%)",
                "severity": "info"
            })
        
        investment_per_transaction = investment / financial_impact.get('additional_transactions', 1)
        
        if investment_per_transaction > 1000:
            warnings.append({
                "type": "high_cac",
                "message": f"Investment per additional transaction (${investment_per_transaction:.0f}) is high",
                "severity": "low"
            })
        
        high_severity_count = len([w for w in warnings if w['severity'] == 'high'])
        
        if high_severity_count > 0:
            assessment = "requires_scrutiny"
            print(f"\n   🔴 ASSESSMENT: Requires executive scrutiny ({high_severity_count} high-severity flags)")
        elif len(warnings) > 2:
            assessment = "needs_validation"
            print(f"\n   🟡 ASSESSMENT: Validate assumptions before proceeding")
        else:
            assessment = "realistic"
            print(f"\n   ✅ ASSESSMENT: Assumptions appear realistic")
        
        if warnings:
            print(f"\n   ⚠️  {len(warnings)} assumption(s) flagged:")
            for w in warnings:
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}
                print(f"   {severity_emoji.get(w['severity'], '•')} {w['message']}")
        
        return {
            "warnings": warnings,
            "assessment": assessment,
            "high_severity_count": high_severity_count,
            "is_realistic": high_severity_count == 0
        }
    
    def _research_benchmarks_resilient(self, expected_lift: float) -> dict:
        """Research benchmarks with retry (Pattern 1)"""
        
        print(f"🔍 Researching benchmarks...")
        
        def safe_search(query: str, num_results: int = 3):
            result = self.tools.web_search(query, num_results)
            if not result.get('success'):
                raise ValueError(f"Search failed: {result.get('error')}")
            return result
        
        # Search with retry
        search_result = self.retry.execute(
            safe_search,
            "personalization conversion lift benchmarks enterprise",
            3
        )
        
        results = search_result.get("results", [])
        print(f"   Found {len(results)} sources")
        
        # Consume budget
        self.budget.consume(300, "research_benchmarks")
        
        return {
            "sources": results,
            "query": search_result.get("query", "")
        }
    
    def _generate_recommendation_resilient(self,
                                          investment: float,
                                          expected_lift: float,
                                          current_data: dict,
                                          financial_impact: dict,
                                          validation: dict,
                                          benchmarks: dict) -> str:
        """Generate recommendation with retry and budget check (Patterns 1, 3)"""
        
        print(f"📝 Generating recommendation...")
        
        # Check budget first (Pattern 3)
        budget_status = self.budget.check_available(2000)
        
        if not budget_status['sufficient']:
            print(f"   ⚠️  Insufficient budget for full recommendation")
            return self._generate_simple_recommendation(
                investment,
                financial_impact,
                validation
            )
        
        simple_roi = (financial_impact['additional_revenue'] / investment - 1) * 100
        payback_period = investment / financial_impact['additional_revenue']
        
        context = f"""Generate a concise executive recommendation (3-4 paragraphs).

Investment: ${investment:,.0f}
Expected lift: +{expected_lift:.1%}
Additional revenue: ${financial_impact['additional_revenue']:,.0f}
ROI: {simple_roi:.0f}%
Payback: {payback_period:.1f} years
Assessment: {validation['assessment']}

Start with "RECOMMEND APPROVAL", "RECOMMEND REJECTION", or "CONDITIONAL APPROVAL".
Be data-driven and action-oriented."""
        
        def generate():
            response = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                temperature=0.4,
                messages=[{"role": "user", "content": context}]
            )
            
            # Consume budget
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            self.budget.consume(tokens_used, "generate_recommendation")
            
            return response.content[0].text
        
        # Generate with retry (Pattern 1)
        recommendation = self.retry.execute(generate)
        
        print(f"   ✅ Generated {len(recommendation)} chars")
        
        return recommendation
    
    def _generate_simple_recommendation(self,
                                       investment: float,
                                       financial_impact: dict,
                                       validation: dict) -> str:
        """Generate simple recommendation without LLM (budget fallback)"""
        
        simple_roi = (financial_impact['additional_revenue'] / investment - 1) * 100
        payback_period = investment / financial_impact['additional_revenue']
        
        if validation['assessment'] == 'requires_scrutiny':
            recommendation_type = "CONDITIONAL APPROVAL"
        elif simple_roi > 50:
            recommendation_type = "RECOMMEND APPROVAL"
        else:
            recommendation_type = "RECOMMEND FURTHER ANALYSIS"
        
        return f"""{recommendation_type}

Investment of ${investment:,.0f} projects {simple_roi:.0f}% ROI with {payback_period:.1f} year payback.

Assessment: {validation['assessment']}. {"High-severity warnings require executive review." if validation['high_severity_count'] > 0 else "Assumptions appear reasonable."}

Track conversion rate, transaction volume, and revenue impact monthly if approved.

[Note: Simplified recommendation due to budget constraints]"""
    
    def _handle_step_failure(self, step_name: str, error: Exception) -> dict:
        """Handle failure of a specific step (Pattern 5)"""
        
        error_id = self.error_logger.log_error(
            error=error,
            context={
                "step": step_name,
                "partial_results": list(self.partial_results.keys()),
                "budget_used": self.budget.usage
            },
            severity="error"
        )
        
        return {
            "status": "partial_failure",
            "failed_step": step_name,
            "error_id": error_id,
            "partial_results": self.partial_results,
            "message": f"Analysis failed at step: {step_name}. Error ID: {error_id}",
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_report(self) -> str:
        """Generate formatted executive report"""
        
        if not self.analysis_data.get("status"):
            return "No analysis completed yet."
        
        if self.analysis_data["status"] != "success":
            return f"Analysis Status: {self.analysis_data['status']}\n{json.dumps(self.analysis_data, indent=2)}"
        
        data = self.analysis_data
        
        simple_roi = (data['financial_impact']['additional_revenue'] / data['investment'] - 1) * 100
        payback_period = data['investment'] / data['financial_impact']['additional_revenue']
        
        report = f"""
{'='*70}
PRODUCTION ROI ANALYSIS
{'='*70}

Status: {data['status'].upper()}
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

EXECUTIVE SUMMARY
-----------------
Investment: ${data['investment']:,.0f}
Expected Lift: +{data['expected_lift']:.1%}
Simple ROI: {simple_roi:.0f}%
Payback Period: {payback_period:.1f} years
Assessment: {data['validation']['assessment'].upper().replace('_', ' ')}

CURRENT PLATFORM METRICS
------------------------
Annual Revenue: ${data['current_data']['revenue']:,.0f}
Conversion Rate: {data['current_data']['conversion_rate']:.2%}
Platform Uptime: {data['current_data']['uptime']:.2%}
Personalization Adoption: {data['current_data']['personalization_engine']['adoption_rate']:.1%}
Active Users: {data['current_data']['personalization_engine']['users']:,}

CONVERSION ECONOMICS
--------------------
Annual Traffic: {data['financial_impact']['annual_traffic']:,} visitors
Current Transactions: {data['financial_impact']['current_transactions']:,.0f}
Average Order Value: ${data['financial_impact']['average_order_value']:,.2f}

PROJECTED FINANCIAL IMPACT
---------------------------
Current Conversion: {data['current_data']['conversion_rate']:.2%}
New Conversion: {data['financial_impact']['new_conversion_rate']:.2%}
Relative Improvement: {data['financial_impact']['relative_lift']:.1%}

Current Transactions: {data['financial_impact']['current_transactions']:,.0f}
New Transactions: {data['financial_impact']['new_transactions']:,.0f}
Additional Transactions: {data['financial_impact']['additional_transactions']:,.0f}

Current Revenue: ${data['current_data']['revenue']:,.0f}
Additional Revenue: ${data['financial_impact']['additional_revenue']:,.0f}
New Total Revenue: ${data['financial_impact']['new_revenue']:,.0f}

Investment per Additional Transaction: ${data['investment'] / data['financial_impact']['additional_transactions']:,.2f}

ASSUMPTION VALIDATION
----------------------
"""
        
        # Add validation assessment
        validation = data.get('validation', {})
        assessment = validation.get('assessment', 'unknown')
        
        if assessment == "requires_scrutiny":
            report += "🔴 HIGH-RISK SCENARIO - REQUIRES EXECUTIVE SCRUTINY\n\n"
        elif assessment == "needs_validation":
            report += "🟡 MODERATE-RISK SCENARIO - VALIDATE BEFORE PROCEEDING\n\n"
        else:
            report += "✅ LOW-RISK SCENARIO - ASSUMPTIONS APPEAR REALISTIC\n\n"
        
        # Add warnings
        warnings = validation.get('warnings', [])
        
        if warnings:
            report += "Flags raised during analysis:\n\n"
            for w in warnings:
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}
                report += f"{severity_emoji.get(w['severity'], '•')} [{w['severity'].upper()}] {w['message']}\n\n"
        else:
            report += "No validation warnings. All assumptions within reasonable ranges.\n\n"
        
        report += f"""
INDUSTRY CONTEXT
----------------
{self._format_benchmarks(data['benchmarks'])}

RECOMMENDATION
--------------
{data['recommendation']}

{'='*70}
Analysis Metadata:
- Total tokens used: {data['metadata']['budget_summary']['usage']:,}
- Budget limit: {data['metadata']['budget_summary']['budget_limit']:,}
- Tool calls made: {data['metadata']['tool_calls']}
- Analysis timestamp: {data['metadata']['timestamp']}
- Resilience: ENABLED ✅
{'='*70}
"""
        
        return report
    
    def _format_benchmarks(self, benchmarks: dict) -> str:
        """Format benchmark data for report"""
        sources = benchmarks.get("sources", [])
        
        if not sources:
            if benchmarks.get("skipped"):
                return "(Benchmark research skipped due to budget constraints)"
            else:
                return "(No benchmark data available)"
        
        formatted = ""
        for source in sources:
            formatted += f"- {source['snippet']}\n"
        
        return formatted
    
    def save_report(self, filename: str = None) -> str:
        """Save report to file"""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"roi_analysis_{timestamp}.txt"
        
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"\n💾 Report saved to {filename}")
        
        return filename


# DEMOS

def demo_basic_roi():
    """Demo 1: Basic ROI analysis"""
    
    print("\n" + "💼 " * 20)
    print("DEMO 1: Basic ROI Analysis")
    print("💼 " * 20)
    
    analyzer = ProductionROIAnalyzer(annual_traffic=1000000, token_budget=30000)
    
    results = analyzer.analyze(
        investment_amount=500000,
        expected_conversion_lift=0.006,
        scenario_description="Invest in AI personalization improvements"
    )
    
    # Display report
    report = analyzer.generate_report()
    print("\n" + report)
    
    # Save to file
    analyzer.save_report()


def demo_high_investment():
    """Demo 2: High investment scenario"""
    
    print("\n" + "💼 " * 20)
    print("DEMO 2: High Investment Scenario")
    print("💼 " * 20)
    
    analyzer = ProductionROIAnalyzer(annual_traffic=1000000, token_budget=30000)
    
    results = analyzer.analyze(
        investment_amount=2000000,
        expected_conversion_lift=0.015,
        scenario_description="Major platform overhaul with ML pipeline"
    )
    
    report = analyzer.generate_report()
    print("\n" + report)
    
    analyzer.save_report("roi_high_investment.txt")


def demo_conservative():
    """Demo 3: Conservative scenario"""
    
    print("\n" + "💼 " * 20)
    print("DEMO 3: Conservative Scenario")
    print("💼 " * 20)
    
    analyzer = ProductionROIAnalyzer(annual_traffic=1000000, token_budget=30000)
    
    results = analyzer.analyze(
        investment_amount=250000,
        expected_conversion_lift=0.003,
        scenario_description="Incremental improvements to existing personalization"
    )
    
    report = analyzer.generate_report()
    print("\n" + report)
    
    analyzer.save_report("roi_conservative.txt")


def demo_comparison():
    """Demo 4: Compare multiple scenarios with REALISTIC lifts"""
    
    print("\n" + "💼 " * 20)
    print("DEMO 4: Scenario Comparison (Realistic Lifts)")
    print("💼 " * 20)
    
    print("\n💡 Using realistic conversion lifts:")
    print("   - Conservative: +0.3% absolute (~9% relative)")
    print("   - Moderate: +0.6% absolute (~19% relative)")
    print("   - Aggressive: +1.0% absolute (~31% relative)\n")
    
    scenarios = [
        {
            "investment": 250000, 
            "lift": 0.003,
            "name": "Conservative"
        },
        {
            "investment": 500000, 
            "lift": 0.006,
            "name": "Moderate"
        },
        {
            "investment": 1000000, 
            "lift": 0.010,
            "name": "Aggressive"
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"\n\nAnalyzing {scenario['name']} scenario...")
        analyzer = ProductionROIAnalyzer(annual_traffic=1000000, token_budget=30000)
        
        result = analyzer.analyze(
            investment_amount=scenario["investment"],
            expected_conversion_lift=scenario["lift"],
            scenario_description=f"{scenario['name']} investment approach"
        )
        
        if result['status'] == 'success':
            roi = (result["financial_impact"]["additional_revenue"] / scenario["investment"] - 1) * 100
            payback = scenario["investment"] / result["financial_impact"]["additional_revenue"]
            
            results.append({
                "name": scenario["name"],
                "investment": scenario["investment"],
                "lift": scenario["lift"],
                "relative_lift": result["financial_impact"]["relative_lift"],
                "additional_revenue": result["financial_impact"]["additional_revenue"],
                "roi": roi,
                "payback": payback,
                "assessment": result["validation"]["assessment"],
                "high_warnings": result["validation"]["high_severity_count"]
            })
    
    # Print comparison
    print("\n" + "="*110)
    print("SCENARIO COMPARISON")
    print("="*110)
    print(f"\n{'Scenario':<15} {'Investment':<15} {'Abs Lift':<12} {'Rel Lift':<12} {'Add Revenue':<15} {'ROI':<10} {'Payback':<10} {'Assessment':<20}")
    print("-" * 110)
    
    for r in results:
        assessment_emoji = {
            "realistic": "✅",
            "needs_validation": "🟡",
            "requires_scrutiny": "🔴"
        }
        emoji = assessment_emoji.get(r['assessment'], "")
        
        print(f"{r['name']:<15} ${r['investment']:>13,.0f} {r['lift']:>10.1%} {r['relative_lift']:>10.1%} ${r['additional_revenue']:>13,.0f} {r['roi']:>8.0f}% {r['payback']:>8.1f}y  {emoji} {r['assessment']:<18}")


def demo_invalid_input():
    """Demo 5: Test input validation"""
    
    print("\n" + "💼 " * 20)
    print("DEMO 5: Input Validation")
    print("💼 " * 20)
    
    analyzer = ProductionROIAnalyzer()
    
    # Test invalid input
    print("\nTest 1: Negative investment")
    result1 = analyzer.analyze(
        investment_amount=-500000,
        expected_conversion_lift=0.02
    )
    print(f"Status: {result1['status']}")
    if result1.get('errors'):
        print(f"Errors: {result1['errors']}")
    
    # Test unrealistic lift
    print("\nTest 2: Unrealistic conversion lift")
    analyzer2 = ProductionROIAnalyzer()
    result2 = analyzer2.analyze(
        investment_amount=500000,
        expected_conversion_lift=0.15  # 15% is way too high
    )
    print(f"Status: {result2['status']}")
    if result2.get('errors'):
        print(f"Errors: {result2['errors']}")


if __name__ == "__main__":
    print("\n" + "📊 " * 20)
    print("PRODUCTION ROI ANALYZER - FULL DEMO")
    print("📊 " * 20)
    
    print("\nChoose demo:")
    print("1. Basic ROI analysis ($500K, +0.6%)")
    print("2. High investment ($2M, +1.5%)")
    print("3. Conservative ($250K, +0.3%)")
    print("4. Compare all scenarios")
    print("5. Test input validation")
    
    choice = input("\nChoice (1-5): ").strip()
    
    if choice == "1":
        demo_basic_roi()
    elif choice == "2":
        demo_high_investment()
    elif choice == "3":
        demo_conservative()
    elif choice == "4":
        demo_comparison()
    elif choice == "5":
        demo_invalid_input()
    else:
        print("Running demo 4 (comparison)")
        demo_comparison()
    
    print("\n\n✅ Analysis complete!")