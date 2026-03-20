# -*- coding: utf-8 -*-
"""Pydantic models for Zektrix UK Competition Platform"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    balance: float
    role: str
    picture: Optional[str] = None
    created_at: datetime

class QualificationQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int

class PostalEntry(BaseModel):
    company_name: str = "Zektrix UK Ltd"
    address_line1: str = "c/o Bartle House"
    address_line2: str = "Oxford Court, Manchester"
    postcode: str = "M23 WQ"
    country: str = "United Kingdom"
    instructions: List[str] = [
        "Nume complet",
        "Adresă poștală",
        "Email + Telefon",
        "Numele competiției"
    ]

class CompetitionCreate(BaseModel):
    title: str
    description: str
    ticket_price: float
    max_tickets: int
    competition_type: str
    category: Optional[str] = "other"
    image_url: Optional[str] = None
    prize_description: Optional[str] = None
    draw_date: Optional[str] = None
    qualification_question: Optional[QualificationQuestion] = None
    is_free: Optional[bool] = False
    instant_prizes: Optional[List[dict]] = None

class CompetitionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ticket_price: Optional[float] = None
    max_tickets: Optional[int] = None
    competition_type: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    image_url: Optional[str] = None
    prize_description: Optional[str] = None
    draw_date: Optional[str] = None
    qualification_question: Optional[QualificationQuestion] = None
    postal_entry: Optional[PostalEntry] = None
    is_free: Optional[bool] = None
    instant_prizes: Optional[List[dict]] = None

class CompetitionResponse(BaseModel):
    competition_id: str
    title: str
    description: str
    ticket_price: float
    max_tickets: int
    sold_tickets: int
    competition_type: str
    category: Optional[str] = "other"
    status: str
    image_url: Optional[str] = None
    prize_description: Optional[str] = None
    draw_date: Optional[str] = None
    created_at: datetime
    winner_id: Optional[str] = None
    winner_ticket: Optional[int] = None
    qualification_question: Optional[QualificationQuestion] = None
    postal_entry: Optional[PostalEntry] = None
    is_free: Optional[bool] = False
    instant_prizes: Optional[List[dict]] = None

class TicketPurchase(BaseModel):
    competition_id: str
    quantity: int
    qualification_answer: Optional[int] = None

class CartItem(BaseModel):
    competition_id: str
    quantity: int
    qualification_answer: Optional[int] = None

class CartPurchase(BaseModel):
    items: List[CartItem]
    payment_method: str = "wallet"

class TicketResponse(BaseModel):
    ticket_id: str
    user_id: str
    competition_id: str
    ticket_number: int
    purchased_at: datetime
    competition_title: Optional[str] = None
    competition_image: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    
    class Config:
        extra = "allow"

class WalletDeposit(BaseModel):
    amount: float

class TransactionResponse(BaseModel):
    transaction_id: str
    user_id: str
    transaction_type: str
    amount: float
    status: str
    description: Optional[str] = None
    created_at: datetime

class WinnerCreate(BaseModel):
    competition_id: str
    user_id: str
    ticket_number: int
    prize_description: Optional[str] = None

class WinnerResponse(BaseModel):
    winner_id: str
    competition_id: str
    competition_title: str
    user_id: str
    username: str
    ticket_number: int
    prize_description: Optional[str] = None
    announced_at: datetime
    is_automatic: bool

class AdminUserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    balance: Optional[float] = None
    is_blocked: Optional[bool] = None
    new_password: Optional[str] = None

class TicketSearchResult(BaseModel):
    username: str
    tickets: List[TicketResponse]

class ReferralCreate(BaseModel):
    referrer_code: str

class ReferralResponse(BaseModel):
    referral_id: str
    referrer_id: str
    referred_id: str
    status: str
    bonus_amount: float
    created_at: datetime

class AnalyticsResponse(BaseModel):
    total_revenue: float
    total_users: int
    total_tickets: int
    total_competitions: int
    active_competitions: int
    completed_competitions: int
    total_winners: int
    avg_tickets_per_user: float
    revenue_by_day: List[dict]
    top_competitions: List[dict]

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict

class NotificationPreferences(BaseModel):
    push_enabled: bool = True
    competition_alerts: bool = True
    winner_alerts: bool = True

class SpinResult(BaseModel):
    prize_type: str
    prize_value: float
    message: str

class FlashSaleCreate(BaseModel):
    competition_id: str
    discount_percent: int = 20
    duration_hours: int = 2

class ChatMessage(BaseModel):
    message: str
    is_faq: bool = False

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    username: Optional[str] = None

class ChatReplyModel(BaseModel):
    message_id: str
    reply: str
