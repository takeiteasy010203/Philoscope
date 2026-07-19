from fastapi import FastAPI, Request, HTTPException, status, Depends, Form, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (http_exception_handler, request_validation_exception_handler)
from schemas import QuestionForm
from fastapi.responses import JSONResponse,  Response, FileResponse, StreamingResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from schemas import CompassResponse
import json
from typing import Annotated
from models import Question, UserSession
from database import Base, engine, get_db
from google import genai
from dotenv import load_dotenv, find_dotenv
from google import genai
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from google.genai import types
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.utils import PlotlyJSONEncoder
from markupsafe import Markup
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import io  # Ensure io is imported for BytesIO
from io import BytesIO, StringIO
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from svglib.svglib import svg2rlg
import uuid
import os
from fastapi.concurrency import run_in_threadpool 
import secrets
from pydantic import field_serializer
from reportlab.lib.units import inch    
from reportlab.platypus import HRFlowable

print(load_dotenv(find_dotenv(), override=True))

logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='a',format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager 
async def lifespan(_app:FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

limiter = Limiter(key_func=get_remote_address)


app = FastAPI(lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) #type: ignore

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")
templates=Jinja2Templates(directory="templates")

load_dotenv()


client = genai.Client()


prompt = """
"Analyze the following philosophical essay. Evaluate where the author stands "
        "on the five spectrums provided in the schema. For each metric, provide a score, "
        "a descriptive label, and the textual evidence/reasoning behind your decision. left_score is the score of the FIRST ideology in the field name.right_score is the score of the SECOND ideology. Both scores must be integers between 0 and 100. left_score + right_score must equal exactly 100."
"""
def generate_chart(question_data: dict):
    data_container = {  
        "left_var": ['<-Individualism', '<-Rationalism', '<-Universalism', '<-Determinism'],
        "right_var": ['Collectivism->', 'Irrationalism->', 'Relativism->', 'Free will->'],
        "right_scores": [],
        "left_scores": [],
        'label_list': [],
        'evidence_list': [],
        }



    for k, v in question_data["philosophical_compass"].items():
        if isinstance(v, str):
            continue
        data_container["left_scores"].append(v['left_score'])
        data_container["right_scores"].append(v['right_score'])
        data_container["label_list"].append(v["label"])
        data_container["evidence_list"].append(v["evidence"])
    

    df = pd.DataFrame(data_container)
    fig = go.Figure()
    combined_var = zip(df['left_var'],df['right_var'])


    df['combined']=[f'{left} | {right}' for left, right in combined_var]

    fig.add_trace(go.Bar(
        y=df["combined"],
        x=(-df["left_scores"]).tolist(),
        orientation="h",
        name="Left",
        customdata=df[["left_var", 'left_scores']].to_numpy(),
        hovertemplate=(
    "%{customdata[0]}: %{customdata[1]}"
    "<extra></extra>"
),
        marker_color="#FB7185"
    ))

    fig.add_trace(go.Bar(
        y=df["combined"],
        x=df["right_scores"].tolist(),
        orientation="h",
        name="Right",
        customdata=df[['right_var', 'right_scores']].to_numpy(),
        hovertemplate="%{customdata[0]}: %{customdata[1]}<extra></extra>",
        marker_color="#3B82F6"
    ))

    fig.add_vline(
        x=0,
        line_width=3,
        line_color="#333333"
    )

    fig.update_layout(
        barmode="relative",
        title=dict(
            text='Philosophical Compass',
            x=0.5,
            xanchor='center',
            font=dict(size=24, color='#0d6efd', family='Arial'),
        ),
        xaxis=dict(
                range=[-100, 100],
                showticklabels=False,  # Ẩn hoàn toàn các con số (labels)
                showgrid=False,        # Ẩn các đường lưới dọc (nếu muốn biểu đồ tối giản)
                zeroline=True,         # Giữ lại vạch đen ở giữa (trục 0)
                zerolinecolor='black' # Tô đậm vạch trục 0 để làm mốc đối xứng
            ),
        xaxis_title="Score",
        yaxis_title="Category",
        yaxis_autorange="reversed",
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white"
        
    )
    graph_data = json.dumps(fig.to_plotly_json()["data"], cls=PlotlyJSONEncoder)
    graph_layout = json.dumps(fig.to_plotly_json()["layout"], cls=PlotlyJSONEncoder)
    img_plot = fig.to_image(format="svg", width=600, height=400).decode("utf-8")
    
   
   
    
    return graph_data, graph_layout, img_plot

##### GENERATE PDF
def generate_pdf(img: str, original: str, date_posted: str, session_id: str, evi_lab_dict: dict) -> bytes:
    pdf_buffer=io.BytesIO()

    image_buffer = io.StringIO(img)
    img_flowable=svg2rlg(image_buffer)


    doc=SimpleDocTemplate(pdf_buffer, pagesize=letter)
    story= []



    styles=getSampleStyleSheet()

    title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=24,
    leading=28,                  
    alignment=1,                 
    textColor=colors.HexColor("#000000"),
    spaceAfter=16            
)

    title_p = Paragraph("REPORT", title_style)

    original_style = ParagraphStyle(
        'CustomStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#000000"),
        spaceAfter=12
    )
    original_p=Paragraph(original, original_style)

    evi_lab_style = ParagraphStyle(
    'CustomStyle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=10,
    leading=16,
    textColor=colors.HexColor('#111111'),
    spaceAfter=5
)

    blank_style = ParagraphStyle(
        'CustomStyle',
        parent=styles['Normal'],
        spaceBefore=3,
        spaceAfter=10
    )

    evi_style = ParagraphStyle(
        'CustomStyle',
        parent=styles['Normal'],
        fontName='Helvetica-bold',
        fontSize=14,

        textColor=colors.HexColor('#111111'),
        spaceAfter=6
    )

    disclaimer_style =ParagraphStyle(
        'CustomStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontsize = 14,
        leading=16,
        textColor=colors.HexColor("#000000"),
        spaceAfter=2
    )


    custom_style1= ParagraphStyle(
        'CustomStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontsize = 8,
        leading=8*1.4,
        textColor=colors.HexColor("#000000"),
        spaceAfter=2
    )

    custom_style1= ParagraphStyle(
        'CustomStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontsize = 12,
        leading=16,
        textColor=colors.HexColor("#333333"),
        spaceAfter=12
    )

    blank_space = Paragraph('', blank_style)
    p_date=Paragraph(f'Date: {date_posted}', custom_style1)
    p_session=Paragraph(f'Session ID: {session_id}', custom_style1)

    story.append(title_p)
    story.append(original_p)
    story.append(HRFlowable(
        width="100%",           # Span across the entire printable page width
        thickness=1.5,          # Line weight in points
        color="#000000",     # Match the title color
        spaceBefore=5,          # Gap above the line
        spaceAfter=15,          # Gap below the line (before subtitle)
        hAlign='CENTER'
    ))
    for k1, v1 in evi_lab_dict["philosophical_compass"].items():
        if isinstance(v1, str):
            continue
        if isinstance(v1,dict):
            lab_p=Paragraph(v1['label'], evi_style)
            evi_p=Paragraph(v1['evidence'], evi_lab_style)
            story.append(lab_p)
            story.append(evi_p)
        story.append(blank_space)
    story.append(img_flowable)
    story.append(p_date)
    story.append(p_session)
    story.append(Paragraph(
        "<i><b>AI Disclosure:</b> This report was generated with AI assistance. "
        "Please verify critical data points before making decisions.</i>", 
        disclaimer_style
    ))
    story.append(Spacer(1,15))

    doc.build(story)
    
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()
 

    return pdf_bytes

@app.get("/")
@limiter.limit("5/minute")
def get_form(request:Request):
    return templates.TemplateResponse(
        request,
        "main.html",
    )

    


@app.post("/")
@limiter.limit("5/minute")
async def handle_form(
        request:Request,
        response: Response,
        db: Annotated[AsyncSession, Depends(get_db)],
        question: str = Form(...),
        
):
    if len(question) > 5000:
        raise HTTPException(status_code=400, detail="Input too long.")
   ######IP and Session ID     
    user_ip=request.client.host if request.client else "Unknown"
    cookie_session = request.cookies.get("my_session")
    ####SOME SECURITY
    if cookie_session is None:
        session_id = secrets.token_hex(32)
        new_session = UserSession(ip_address=user_ip, session_id=session_id) 
        db.add(new_session)
        await db.commit()
        response.set_cookie(
            key="my_session",
            value=session_id,
            httponly=True,
            secure=True,
            samesite='lax',
        )
        

    else:
        result = await db.execute(select(UserSession).where(UserSession.session_id==cookie_session))
        session = result.scalars().first()
        if session is None:
            session_id = secrets.token_hex(32)
            new_session = UserSession(ip_address=user_ip, session_id=session_id) 
            db.add(new_session)
            await db.commit()
            response.set_cookie(
            key="my_session",
            value=session_id,
            httponly=True,
            secure=True,
            samesite='lax',
        )
        else:
          session_id=session.session_id



    ####CHATTING
    try:
        response_ai = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"{prompt}. Here is the text: {question} ",
        config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=CompassResponse,
        temperature=0.1,
    
   
    )
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=503,
            detail='The AI service is temporarily unavailable'
        )
    print(response_ai.text)
    if response_ai.text is None:
        raise HTTPException (
            status_code=500, detail = "Failed to parse"
        )
    
    
    try:
        question_data = json.loads(response_ai.text)
    except json.JSONDecodeError as JDE:
        logger.exception(JDE)
        raise HTTPException(
            status_code=500,
            detail="Invalid response from AI. SORRY!!!"
        )

    json_qdata = question_data['philosophical_compass']    
#######MODEL

    new_question = Question(content=question, response_text=response_ai.text, session_id=session_id)


    summary = question_data["philosophical_compass"]["overall_summary"]
    try:
        db.add(new_question)
        await db.commit()
        await db.refresh(new_question)
    except:
        await db.rollback()
        raise

    graph_data, graph_layout, img_plot = await run_in_threadpool(generate_chart, question_data)
    
   
    return JSONResponse({   
            "json_qdata": json_qdata,
            "graph_data": graph_data,
            "graph_layout": graph_layout,
            "question_data": question_data,
            "question_id": new_question.id,
            "date_posted": new_question.date_posted.isoformat(),
            "response": response_ai.text,
            "summary": summary
        })
    

@app.get('/download/{question_id}')
async def download(
    question_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(Question).where(Question.id==question_id)
    )
    question = result.scalars().first()
    if question is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )
    try: 
        question_data = json.loads(question.response_text)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code= 500,
            detail="Stored response is invalid"
        )
    
    _, _, img_plot=await run_in_threadpool(
        generate_chart,
        question_data
    )
    pdf_bytes = await run_in_threadpool(
        generate_pdf,
        img_plot,
        question.content,
        str(question.date_posted),
        question.session_id,
        question_data
    )

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="report_{question.id}.pdf"'
        }
    )



    







@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    
    logger.exception(exception) 
    print(exception.detail)
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/") or request.url.path.startswith("/download"):
        
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "status_code": exception.status_code,
                "title": exception.status_code,
                "message": message,
            },
            status_code=exception.status_code,
        )
    return JSONResponse(
            status_code=exception.status_code,
            content={
                "detail": exception.detail
            }
        )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_error(request:Request, exception: Exception):
    logger.exception(exception)
    if request.url.path.startswith("/") or request.url.path.startswith("/download"):
        
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
                "title": "TOO MANY REQUESTS",
                "message": "You are moving a bit too fast for our servers to keep up.",
            },
            status_code=429,
        )
       
    return JSONResponse(
        status_code=429,
        content={
            "detail": "You are moving a bit too fast for our servers to keep up."
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exception: Exception):
    
    logger.exception(exception)
    if request.url.path.startswith("/") or request.url.path.startswith("/download"):
        
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "title": "INTERNAL SERVER ERROR",
                "message": "Internal Server Error. We're very sorry",
            },
            status_code=500,
        )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error"
        }
    )

### RequestValidationError Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    logger.exception(exception)
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )





