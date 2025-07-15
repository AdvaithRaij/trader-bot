"""
Telegram Notifier Module for Trading Bot.
Sends daily reports, trade notifications, and alerts via Telegram Bot API.
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import aiohttp
from loguru import logger

from config import get_config
from trade_logger import trade_logger

config = get_config()


class TelegramNotifier:
    """
    Telegram notification system for trading bot updates.
    Sends daily P&L reports, trade alerts, and system notifications.
    """
    
    def __init__(self):
        self.config = config
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.api_base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.session = None
        
        # Message templates
        self.daily_report_template = """
🤖 **Trading Bot Daily Report** 📊
📅 Date: {date}

💰 **P&L Summary:**
• Total P&L: ₹{total_pnl:,.2f} ({pnl_pct:+.2f}%)
• Trades: {total_trades} ({winning_trades}W / {losing_trades}L)
• Win Rate: {win_rate:.1f}%
• Best Trade: ₹{best_trade:,.2f}
• Worst Trade: ₹{worst_trade:,.2f}

📈 **Trading Stats:**
• Decisions Made: {total_decisions}
• Trades Executed: {executed_decisions}
• Execution Rate: {execution_rate:.1f}%
• Avg Win: ₹{avg_win:,.2f}
• Avg Loss: ₹{avg_loss:,.2f}

🛡️ **Risk Metrics:**
• Max Single Loss: ₹{max_loss:,.2f}
• Max Single Gain: ₹{max_gain:,.2f}
• Avg Trade Duration: {avg_duration:.0f} min

📋 **Top Trades:**
{top_trades}

🎯 **Status:** {status}
⚠️ Generated at {generated_time}
        """
        
        self.trade_alert_template = """
🚨 **Trade Alert** 🚨

📊 Symbol: {symbol}
🎯 Action: {action}
💵 Price: ₹{price:,.2f}
📦 Quantity: {quantity}
💰 Value: ₹{value:,.2f}

📈 Entry: ₹{entry_price:,.2f}
🛑 Stop Loss: ₹{stop_loss:,.2f}
🎯 Target: ₹{target:,.2f}
📊 R:R Ratio: {rr_ratio:.2f}

🤖 AI Confidence: {confidence:.1%}
🧠 Reasoning: {reasoning}

⏰ {timestamp}
        """
        
        self.risk_alert_template = """
⚠️ **Risk Alert** ⚠️

🚨 Event: {event_type}
📝 Description: {description}
⚡ Severity: {severity}

📊 Account Status:
• Available Capital: ₹{available_capital:,.2f}
• Daily P&L: ₹{daily_pnl:,.2f}
• Active Trades: {active_trades}
• Daily Losses: {daily_loss_count}

⏰ {timestamp}
        """
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def is_configured(self) -> bool:
        """Check if Telegram is properly configured."""
        return bool(self.bot_token and self.chat_id)
    
    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message via Telegram Bot API.
        
        Args:
            text: Message text
            parse_mode: Parse mode (Markdown/HTML)
            
        Returns:
            Success status
        """
        if not self.is_configured():
            logger.warning("Telegram not configured - message not sent")
            logger.info(f"[TELEGRAM] {text}")
            return False
        
        try:
            url = f"{self.api_base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info("✅ Telegram message sent successfully")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Telegram API error: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    async def send_daily_report(self, date: datetime = None) -> bool:
        """
        Send daily trading report.
        
        Args:
            date: Date for report (defaults to today)
            
        Returns:
            Success status
        """
        try:
            if date is None:
                date = datetime.now().date()
            
            logger.info(f"📊 Generating daily report for {date}")
            
            # Generate report from trade logger
            report = await trade_logger.generate_daily_report(date)
            
            if not report:
                logger.warning("No report data available")
                return False
            
            # Extract data for template
            trade_summary = report.get('trade_summary', {})
            decision_summary = report.get('decision_summary', {})
            risk_metrics = report.get('risk_metrics', {})
            trades = report.get('trades', [])
            
            # Format top trades
            top_trades = self.format_top_trades(trades[:3])  # Top 3 trades
            
            # Determine status
            status = self.determine_trading_status(trade_summary)
            
            # Fill template
            message = self.daily_report_template.format(
                date=date.strftime('%d %b %Y'),
                total_pnl=trade_summary.get('total_pnl', 0),
                pnl_pct=trade_summary.get('total_pnl_pct', 0),
                total_trades=trade_summary.get('total_trades', 0),
                winning_trades=trade_summary.get('winning_trades', 0),
                losing_trades=trade_summary.get('losing_trades', 0),
                win_rate=trade_summary.get('win_rate_pct', 0),
                best_trade=max([t.get('pnl', 0) for t in trades], default=0),
                worst_trade=min([t.get('pnl', 0) for t in trades], default=0),
                total_decisions=decision_summary.get('total_decisions', 0),
                executed_decisions=decision_summary.get('executed_decisions', 0),
                execution_rate=decision_summary.get('execution_rate_pct', 0),
                avg_win=trade_summary.get('avg_win', 0),
                avg_loss=trade_summary.get('avg_loss', 0),
                max_loss=risk_metrics.get('max_single_loss', 0),
                max_gain=risk_metrics.get('max_single_gain', 0),
                avg_duration=risk_metrics.get('avg_trade_duration_min', 0),
                top_trades=top_trades,
                status=status,
                generated_time=datetime.now().strftime('%H:%M:%S')
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            return False
    
    def format_top_trades(self, trades: List[Dict]) -> str:
        """Format top trades for display."""
        if not trades:
            return "No trades today"
        
        formatted_trades = []
        for i, trade in enumerate(trades, 1):
            symbol = trade.get('symbol', 'UNKNOWN')
            pnl = trade.get('pnl', 0)
            pnl_pct = trade.get('pnl_pct', 0)
            transaction_type = trade.get('transaction_type', 'BUY')
            
            emoji = "📈" if pnl > 0 else "📉"
            formatted_trades.append(
                f"{emoji} {i}. {symbol}: {transaction_type} → ₹{pnl:,.2f} ({pnl_pct:+.2f}%)"
            )
        
        return "\n".join(formatted_trades)
    
    def determine_trading_status(self, trade_summary: Dict) -> str:
        """Determine trading status based on performance."""
        total_pnl = trade_summary.get('total_pnl', 0)
        win_rate = trade_summary.get('win_rate_pct', 0)
        total_trades = trade_summary.get('total_trades', 0)
        
        if total_trades == 0:
            return "No trading activity"
        elif total_pnl > 1000 and win_rate > 70:
            return "Excellent performance! 🚀"
        elif total_pnl > 0 and win_rate > 50:
            return "Positive day 👍"
        elif total_pnl > -500:
            return "Minor losses 📊"
        else:
            return "Significant losses ⚠️"
    
    async def send_trade_alert(self, trade_data: Dict) -> bool:
        """
        Send trade execution alert.
        
        Args:
            trade_data: Trade execution data
            
        Returns:
            Success status
        """
        try:
            # Extract data
            symbol = trade_data.get('symbol', 'UNKNOWN')
            action = trade_data.get('transaction_type', 'UNKNOWN')
            price = trade_data.get('executed_price', 0)
            quantity = trade_data.get('quantity', 0)
            value = price * quantity
            
            ai_decision = trade_data.get('ai_decision', {})
            entry_price = ai_decision.get('entry_price', price)
            stop_loss = ai_decision.get('stop_loss', 0)
            target = ai_decision.get('target_price', 0)
            rr_ratio = ai_decision.get('risk_reward_ratio', 0)
            confidence = ai_decision.get('confidence', 0)
            reasoning = ai_decision.get('reasoning', 'No reasoning provided')
            
            # Format message
            message = self.trade_alert_template.format(
                symbol=symbol,
                action=action,
                price=price,
                quantity=quantity,
                value=value,
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                rr_ratio=rr_ratio,
                confidence=confidence,
                reasoning=reasoning[:100] + "..." if len(reasoning) > 100 else reasoning,
                timestamp=datetime.now().strftime('%d %b %Y %H:%M:%S')
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending trade alert: {e}")
            return False
    
    async def send_risk_alert(self, event_type: str, description: str,
                            severity: str = "WARNING", additional_data: Dict = None) -> bool:
        """
        Send risk management alert.
        
        Args:
            event_type: Type of risk event
            description: Event description
            severity: Severity level
            additional_data: Additional data
            
        Returns:
            Success status
        """
        try:
            # Get current account status (mock for now)
            account_data = additional_data or {}
            
            message = self.risk_alert_template.format(
                event_type=event_type,
                description=description,
                severity=severity,
                available_capital=account_data.get('available_capital', 0),
                daily_pnl=account_data.get('daily_pnl', 0),
                active_trades=account_data.get('active_trades', 0),
                daily_loss_count=account_data.get('daily_loss_count', 0),
                timestamp=datetime.now().strftime('%d %b %Y %H:%M:%S')
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending risk alert: {e}")
            return False
    
    async def send_startup_notification(self) -> bool:
        """Send bot startup notification."""
        message = """
🤖 **Trading Bot Started** 🚀

✅ All systems initialized
📊 Ready for market analysis
🎯 Waiting for trading opportunities

Configuration:
• Capital: ₹{capital:,.2f}
• Max trades: {max_trades}
• Risk per trade: {risk_per_trade:.1%}
• AI confidence threshold: {ai_threshold:.1%}

⏰ Started at {timestamp}
        """.format(
            capital=config.INITIAL_CAPITAL,
            max_trades=config.MAX_ACTIVE_TRADES,
            risk_per_trade=config.MAX_CAPITAL_PER_TRADE,
            ai_threshold=config.AI_CONFIDENCE_THRESHOLD,
            timestamp=datetime.now().strftime('%d %b %Y %H:%M:%S')
        )
        
        return await self.send_message(message)
    
    async def send_shutdown_notification(self, reason: str = "Manual stop") -> bool:
        """Send bot shutdown notification."""
        message = f"""
🛑 **Trading Bot Stopped**

Reason: {reason}
⏰ Stopped at {datetime.now().strftime('%d %b %Y %H:%M:%S')}

📊 Session summary will be sent shortly.
        """
        
        return await self.send_message(message)
    
    async def send_market_close_summary(self) -> bool:
        """Send end-of-day market close summary."""
        try:
            # Get today's report
            report = await trade_logger.generate_daily_report()
            
            if not report:
                return await self.send_message("📊 No trading activity today")
            
            trade_summary = report.get('trade_summary', {})
            
            message = f"""
🔔 **Market Close Summary**

📅 Date: {datetime.now().strftime('%d %b %Y')}

📊 **Quick Stats:**
• Total P&L: ₹{trade_summary.get('total_pnl', 0):,.2f}
• Trades: {trade_summary.get('total_trades', 0)}
• Win Rate: {trade_summary.get('win_rate_pct', 0):.1f}%

🤖 All positions closed
💤 Bot entering sleep mode

📈 Detailed report will follow
            """
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending market close summary: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test Telegram connection."""
        if not self.is_configured():
            logger.warning("Telegram not configured")
            return False
        
        test_message = f"""
🧪 **Test Message**

✅ Telegram connection working
⏰ {datetime.now().strftime('%d %b %Y %H:%M:%S')}

🤖 Trading bot communication test successful!
        """
        
        return await self.send_message(test_message)


# Global notifier instance
notifier = TelegramNotifier()


async def send_daily_report(date: datetime = None) -> bool:
    """Send daily report via Telegram."""
    async with notifier:
        return await notifier.send_daily_report(date)


async def send_trade_alert(trade_data: Dict) -> bool:
    """Send trade alert via Telegram."""
    async with notifier:
        return await notifier.send_trade_alert(trade_data)


async def send_risk_alert(event_type: str, description: str,
                         severity: str = "WARNING", additional_data: Dict = None) -> bool:
    """Send risk alert via Telegram."""
    async with notifier:
        return await notifier.send_risk_alert(event_type, description, severity, additional_data)


if __name__ == "__main__":
    # Test the Telegram notifier
    async def test_notifier():
        try:
            async with TelegramNotifier() as telegram:
                # Test connection
                success = await telegram.test_connection()
                print(f"Connection test: {'✅' if success else '❌'}")
                
                # Test daily report (mock data)
                if config.MOCK_MODE:
                    print("📊 Testing with mock data...")
                    
                    # Mock trade data for testing
                    mock_trade = {
                        'symbol': 'RELIANCE',
                        'transaction_type': 'BUY',
                        'executed_price': 2500.0,
                        'quantity': 10,
                        'ai_decision': {
                            'entry_price': 2500.0,
                            'stop_loss': 2450.0,
                            'target_price': 2600.0,
                            'risk_reward_ratio': 2.0,
                            'confidence': 0.85,
                            'reasoning': 'Strong bullish signals detected with high volume and positive sentiment'
                        }
                    }
                    
                    # Test trade alert
                    trade_success = await telegram.send_trade_alert(mock_trade)
                    print(f"Trade alert: {'✅' if trade_success else '❌'}")
                    
                    # Test risk alert
                    risk_success = await telegram.send_risk_alert(
                        "MAX_TRADES_REACHED",
                        "Maximum number of active trades reached",
                        "WARNING",
                        {'available_capital': 95000, 'active_trades': 2}
                    )
                    print(f"Risk alert: {'✅' if risk_success else '❌'}")
                    
                    # Test startup notification
                    startup_success = await telegram.send_startup_notification()
                    print(f"Startup notification: {'✅' if startup_success else '❌'}")
                
        except Exception as e:
            logger.error(f"Test failed: {e}")
    
    asyncio.run(test_notifier())
