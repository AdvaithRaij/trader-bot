"""
Email Notification System for Trading Bot.
Sends alerts for trade executions, SL/TP hits, and daily P&L summaries.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, List
from loguru import logger

from config import get_config

config = get_config()


class EmailNotifier:
    """
    Email notification service using SMTP.
    
    Supports Gmail, Outlook, or custom SMTP servers.
    """
    
    def __init__(self):
        self.smtp_server = config.SMTP_SERVER if hasattr(config, 'SMTP_SERVER') else "smtp.gmail.com"
        self.smtp_port = config.SMTP_PORT if hasattr(config, 'SMTP_PORT') else 587
        self.sender_email = config.SENDER_EMAIL if hasattr(config, 'SENDER_EMAIL') else None
        self.sender_password = config.SENDER_PASSWORD if hasattr(config, 'SENDER_PASSWORD') else None
        self.recipient_email = config.RECIPIENT_EMAIL if hasattr(config, 'RECIPIENT_EMAIL') else None
        
        self.is_configured = bool(self.sender_email and self.sender_password and self.recipient_email)
        
        if self.is_configured:
            logger.info("✅ Email notifier configured")
        else:
            logger.warning("⚠️ Email notifier not configured - set SMTP credentials in .env")
    
    async def send_email(
        self,
        subject: str,
        body: str,
        is_html: bool = True
    ) -> bool:
        """
        Send an email notification.
        
        Args:
            subject: Email subject
            body: Email body (HTML or plain text)
            is_html: Whether body is HTML
            
        Returns:
            True if sent successfully
        """
        if not self.is_configured:
            logger.warning("Email not configured - skipping notification")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"[Trading Bot] {subject}"
            message["From"] = self.sender_email
            message["To"] = self.recipient_email
            
            # Add body
            content_type = "html" if is_html else "plain"
            message.attach(MIMEText(body, content_type))
            
            # Create secure connection
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, message.as_string())
            
            logger.info(f"📧 Email sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False
    
    async def notify_trade_executed(self, trade: Dict) -> bool:
        """Send notification when a trade is executed."""
        subject = f"🟢 Trade Executed: {trade.get('symbol', 'Unknown')}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #1e222d; color: #d1d4dc; padding: 20px;">
            <h2 style="color: #26a69a;">Trade Executed</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #363a45;"><strong>Symbol:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #363a45;">{trade.get('symbol', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #363a45;"><strong>Direction:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #363a45;">{trade.get('direction', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #363a45;"><strong>Entry Price:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #363a45;">₹{trade.get('entryPrice', 0):,.2f}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #363a45;"><strong>Quantity:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #363a45;">{trade.get('quantity', 0)}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #363a45;"><strong>Stop Loss:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #363a45;">₹{trade.get('stopLoss', 0):,.2f}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #363a45;"><strong>Target:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #363a45;">₹{trade.get('target1', 0):,.2f}</td></tr>
            </table>
            <p style="color: #787b86; font-size: 12px; margin-top: 20px;">
                Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </body>
        </html>
        """
        
        return await self.send_email(subject, body)
    
    async def notify_trade_closed(self, trade: Dict) -> bool:
        """Send notification when a trade is closed."""
        pnl = trade.get('pnl', 0)
        pnl_color = "#26a69a" if pnl >= 0 else "#ef5350"
        emoji = "🟢" if pnl >= 0 else "🔴"
        
        subject = f"{emoji} Trade Closed: {trade.get('symbol', 'Unknown')} | P&L: ₹{pnl:,.2f}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #1e222d; color: #d1d4dc; padding: 20px;">
            <h2 style="color: {pnl_color};">Trade Closed</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #363a45;"><strong>Symbol:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #363a45;">{trade.get('symbol', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #363a45;"><strong>Exit Price:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #363a45;">₹{trade.get('exitPrice', 0):,.2f}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #363a45;"><strong>Exit Reason:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #363a45;">{trade.get('exitReason', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #363a45;"><strong>P&L:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #363a45; color: {pnl_color};">
                        ₹{pnl:,.2f} ({trade.get('pnlPercent', 0):.2f}%)</td></tr>
            </table>
        </body>
        </html>
        """

        return await self.send_email(subject, body)

    async def notify_stop_loss_hit(self, symbol: str, price: float, loss: float) -> bool:
        """Send urgent notification when stop loss is hit."""
        subject = f"🔴 STOP LOSS HIT: {symbol} | Loss: ₹{abs(loss):,.2f}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #1e222d; color: #d1d4dc; padding: 20px;">
            <h2 style="color: #ef5350;">⚠️ Stop Loss Triggered</h2>
            <p><strong>Symbol:</strong> {symbol}</p>
            <p><strong>Exit Price:</strong> ₹{price:,.2f}</p>
            <p><strong>Loss:</strong> <span style="color: #ef5350;">₹{abs(loss):,.2f}</span></p>
            <p style="color: #787b86;">Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """

        return await self.send_email(subject, body)

    async def notify_daily_summary(self, summary: Dict) -> bool:
        """Send daily P&L summary."""
        total_pnl = summary.get('total_pnl', 0)
        pnl_color = "#26a69a" if total_pnl >= 0 else "#ef5350"

        subject = f"📊 Daily Summary | P&L: ₹{total_pnl:,.2f}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #1e222d; color: #d1d4dc; padding: 20px;">
            <h2>📊 Daily Trading Summary</h2>
            <h3 style="color: {pnl_color};">Total P&L: ₹{total_pnl:,.2f}</h3>

            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <tr><td style="padding: 8px;"><strong>Total Trades:</strong></td>
                    <td style="padding: 8px;">{summary.get('total_trades', 0)}</td></tr>
                <tr><td style="padding: 8px;"><strong>Winning Trades:</strong></td>
                    <td style="padding: 8px; color: #26a69a;">{summary.get('winning_trades', 0)}</td></tr>
                <tr><td style="padding: 8px;"><strong>Losing Trades:</strong></td>
                    <td style="padding: 8px; color: #ef5350;">{summary.get('losing_trades', 0)}</td></tr>
                <tr><td style="padding: 8px;"><strong>Win Rate:</strong></td>
                    <td style="padding: 8px;">{summary.get('win_rate', 0):.1f}%</td></tr>
            </table>
        </body>
        </html>
        """

        return await self.send_email(subject, body)

    async def notify_circuit_breaker(self, reason: str) -> bool:
        """Send urgent notification when circuit breaker triggers."""
        subject = f"🛑 TRADING HALTED: {reason}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #1e222d; color: #d1d4dc; padding: 20px;">
            <h2 style="color: #ef5350;">🛑 Circuit Breaker Triggered</h2>
            <p><strong>Reason:</strong> {reason}</p>
            <p>All trading has been halted. Please review.</p>
            <p style="color: #787b86;">Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """

        return await self.send_email(subject, body)


# Global email notifier instance
email_notifier = EmailNotifier()
