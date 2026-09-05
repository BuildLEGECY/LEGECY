import asyncio,logging,os,time,uuid
from pathlib import Path
from typing import Any,Dict,Optional
from dotenv import load_dotenv
from fastapi import FastAPI,HTTPException,Query,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,HTMLResponse
from pydantic import BaseModel,Field
from solders.pubkey import Pubkey
from smart_wallet_discovery import discover_smart_wallets
from smart_money_ranking import rank_smart_wallets
from wallet_comparison import compare_wallet_profiles
from wallet_intelligence_fast import build_wallet_profile
from wallet_profile import build_profile_summary
from watchlist_api import router as watchlist_router
load_dotenv()
APP_ENV=os.getenv('APP_ENV','development').strip().lower();API_VERSION='2.2.0';BASE_DIR=Path(__file__).resolve().parent;DASHBOARD_FILE=BASE_DIR/'dashboard'/'index.html';DASHBOARD_ENHANCEMENTS=BASE_DIR/'dashboard'/'dashboard_enhancements.js'
RATE_LIMIT_REQUESTS=int(os.getenv('RATE_LIMIT_REQUESTS','20'));RATE_LIMIT_WINDOW_SECONDS=int(os.getenv('RATE_LIMIT_WINDOW_SECONDS','60'));ANALYSIS_TIMEOUT_SECONDS=int(os.getenv('ANALYSIS_TIMEOUT_SECONDS','45'));CACHE_TTL_SECONDS=int(os.getenv('CACHE_TTL_SECONDS','15'));CACHE_MAX_ENTRIES=int(os.getenv('CACHE_MAX_ENTRIES','100'));DEFAULT_HISTORY_LIMIT=int(os.getenv('DEFAULT_HISTORY_LIMIT','20'));MAX_HISTORY_LIMIT=int(os.getenv('MAX_HISTORY_LIMIT','100'));DEFAULT_HISTORY_LIMIT=max(1,min(DEFAULT_HISTORY_LIMIT,MAX_HISTORY_LIMIT));MAX_HISTORY_LIMIT=max(DEFAULT_HISTORY_LIMIT,MAX_HISTORY_LIMIT)
_rate_limit_state={};_wallet_cache={};_metrics={'requests_total':0,'responses_2xx':0,'responses_4xx':0,'responses_5xx':0,'wallet_analysis_requests':0,'wallet_analysis_success':0,'wallet_analysis_errors':0,'wallet_analysis_timeouts':0,'rate_limit_rejections':0,'cache_hits':0,'cache_misses':0,'total_response_time_ms':0.0,'wallet_analysis_time_ms':0.0,'comparison_requests':0,'comparison_success':0,'comparison_errors':0,'discovery_requests':0,'discovery_success':0,'discovery_errors':0,'ranking_requests':0,'ranking_success':0,'ranking_errors':0}
CORS_ORIGINS=[x.strip() for x in os.getenv('CORS_ORIGINS','http://127.0.0.1:5500,http://localhost:5500').split(',') if x.strip()];logging.basicConfig(level=os.getenv('LOG_LEVEL','INFO').upper());logger=logging.getLogger('legecy-api')
class ErrorResponse(BaseModel): message:str=Field(description='Human-readable error message.')
class WalletProfileResponse(BaseModel):
 wallet:Optional[str]=None;analysis:Dict[str,Any]={};activity:Dict[str,Any]={};swap_metrics:Dict[str,Any]={};trading:Dict[str,Any]={};trade_performance:Dict[str,Any]={};behavior:Dict[str,Any]={};protocols:Dict[str,Any]={};reputation:Dict[str,Any]={};smart_money:Dict[str,Any]={};data_confidence:Dict[str,Any]={};generated_at:Optional[str]=None;cache:Dict[str,Any]={}
class WalletComparisonResponse(BaseModel):
 wallet_a:Optional[str]=None;wallet_b:Optional[str]=None;winner:Dict[str,Any]={};composite:Dict[str,Any]={};metrics:Dict[str,Any]={};confidence:Dict[str,Any]={}
class WalletDiscoveryResponse(BaseModel):
 seed_wallet:Optional[str]=None;history_scanned:int=0;candidates:list[Dict[str,Any]]=[];discovery:Dict[str,Any]={}
app=FastAPI(title='LEGECY Wallet Intelligence API',description='Public API for Solana wallet intelligence, reputation, trading behavior, data confidence, smart-money analysis, wallet comparison, smart-wallet discovery, smart-money ranking and watchlists.',version=API_VERSION,docs_url='/docs',redoc_url='/redoc',openapi_url='/openapi.json',contact={'name':'LEGECY'},license_info={'name':'Project License'})
app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS,allow_credentials=True,allow_methods=['GET','POST','DELETE'],allow_headers=['*'])
app.include_router(watchlist_router)
@app.middleware('http')
async def request_logging_middleware(request:Request,call_next):
 rid=str(uuid.uuid4());start=time.perf_counter();_metrics['requests_total']+=1
 try:
  response=await call_next(request);duration=(time.perf_counter()-start)*1000;_metrics['total_response_time_ms']+=duration;code=response.status_code
  if 200<=code<300:_metrics['responses_2xx']+=1
  elif 400<=code<500:_metrics['responses_4xx']+=1
  elif code>=500:_metrics['responses_5xx']+=1
  response.headers['X-Request-ID']=rid;response.headers['X-Response-Time-MS']=f'{duration:.2f}';return response
 except Exception:
  duration=(time.perf_counter()-start)*1000;_metrics['total_response_time_ms']+=duration;_metrics['responses_5xx']+=1;logger.exception('request_id=%s path=%s status=500 duration_ms=%.2f',rid,request.url.path,duration);raise
def validate_wallet_address(wallet_address:str)->str:
 wallet_address=wallet_address.strip()
 if not wallet_address:raise HTTPException(status_code=400,detail={'message':'Wallet address is required.'})
 try:Pubkey.from_string(wallet_address)
 except (ValueError,TypeError):raise HTTPException(status_code=400,detail={'message':'Invalid Solana wallet address.'})
 return wallet_address
def check_rate_limit(request:Request):
 now=time.monotonic();ip=request.client.host if request.client else 'unknown';started,count=_rate_limit_state.get(ip,(now,0))
 if now-started>=RATE_LIMIT_WINDOW_SECONDS:started,count=now,0
 if count>=RATE_LIMIT_REQUESTS:
  _metrics['rate_limit_rejections']+=1;retry=max(1,int(RATE_LIMIT_WINDOW_SECONDS-(now-started)));raise HTTPException(status_code=429,detail={'message':'Too many wallet analysis requests. Please try again later.'},headers={'Retry-After':str(retry)})
 _rate_limit_state[ip]=(started,count+1)
 if len(_rate_limit_state)>1000:
  cutoff=now-RATE_LIMIT_WINDOW_SECONDS
  for key in [k for k,(s,_) in _rate_limit_state.items() if s<cutoff]:_rate_limit_state.pop(key,None)
def _cache_key(wallet:str,limit:int):return f'{wallet}:{limit}'
def get_cached_wallet_profile(wallet_address:str,history_limit:int=DEFAULT_HISTORY_LIMIT):
 cached=_wallet_cache.get(_cache_key(wallet_address,history_limit))
 if cached is None:return None
 created,profile=cached
 if time.monotonic()-created>=CACHE_TTL_SECONDS:_wallet_cache.pop(_cache_key(wallet_address,history_limit),None);return None
 return profile
def cache_wallet_profile(wallet_address:str,profile,history_limit:int=DEFAULT_HISTORY_LIMIT):
 key=_cache_key(wallet_address,history_limit);_wallet_cache[key]=(time.monotonic(),profile)
 if len(_wallet_cache)>CACHE_MAX_ENTRIES:_wallet_cache.pop(min(_wallet_cache,key=lambda k:_wallet_cache[k][0]),None)
async def _analyze_for_compare(wallet:str,limit:int):
 cached=get_cached_wallet_profile(wallet,limit)
 if cached is not None:_metrics['cache_hits']+=1;return cached
 _metrics['cache_misses']+=1;profile=await build_wallet_profile(wallet,limit=limit);cache_wallet_profile(wallet,profile,limit);return profile
@app.get('/',tags=['Public'],summary='Open the LEGECY dashboard')
async def root():
 if DASHBOARD_FILE.exists():
  html=DASHBOARD_FILE.read_text(encoding='utf-8')
  if DASHBOARD_ENHANCEMENTS.exists() and 'dashboard_enhancements.js' not in html:
   html=html.replace('</body>','<script src="/dashboard-enhancements.js"></script></body>')
  return HTMLResponse(html)
 return {'name':'LEGECY','service':'Solana Wallet Intelligence API','status':'online','version':API_VERSION,'environment':APP_ENV}
@app.get('/dashboard-enhancements.js',tags=['Public'],include_in_schema=False)
async def dashboard_enhancements():
 if not DASHBOARD_ENHANCEMENTS.exists():raise HTTPException(status_code=404,detail={'message':'Dashboard enhancements are not available.'})
 return FileResponse(DASHBOARD_ENHANCEMENTS,media_type='application/javascript')
@app.get('/api',tags=['Public'],summary='Get API information')
async def api_info():return {'name':'LEGECY','service':'Solana Wallet Intelligence API','status':'online','version':API_VERSION,'environment':APP_ENV}
@app.get('/health',tags=['Public'],summary='Check API health')
async def health():return {'status':'ok','service':'legecy-api','version':API_VERSION,'environment':APP_ENV}
@app.get('/metrics',tags=['Public'],summary='Get production metrics')
async def metrics():
 total=_metrics['requests_total'];wr=_metrics['wallet_analysis_requests'];return {'version':API_VERSION,'environment':APP_ENV,'requests':{'total':total,'2xx':_metrics['responses_2xx'],'4xx':_metrics['responses_4xx'],'5xx':_metrics['responses_5xx'],'average_response_time_ms':round(_metrics['total_response_time_ms']/total if total else 0,2)},'wallet_analysis':{'requests':wr,'success':_metrics['wallet_analysis_success'],'errors':_metrics['wallet_analysis_errors'],'timeouts':_metrics['wallet_analysis_timeouts'],'average_time_ms':round(_metrics['wallet_analysis_time_ms']/wr if wr else 0,2)},'comparison':{'requests':_metrics['comparison_requests'],'success':_metrics['comparison_success'],'errors':_metrics['comparison_errors']},'discovery':{'requests':_metrics['discovery_requests'],'success':_metrics['discovery_success'],'errors':_metrics['discovery_errors']},'ranking':{'requests':_metrics['ranking_requests'],'success':_metrics['ranking_success'],'errors':_metrics['ranking_errors']},'cache':{'hits':_metrics['cache_hits'],'misses':_metrics['cache_misses'],'ttl_seconds':CACHE_TTL_SECONDS,'max_entries':CACHE_MAX_ENTRIES},'rate_limit':{'rejections':_metrics['rate_limit_rejections'],'requests_per_window':RATE_LIMIT_REQUESTS,'window_seconds':RATE_LIMIT_WINDOW_SECONDS},'history':{'default_limit':DEFAULT_HISTORY_LIMIT,'max_limit':MAX_HISTORY_LIMIT}}
@app.get('/wallet/{wallet_address}',tags=['Wallet Intelligence'],summary='Analyze a Solana wallet',response_model=WalletProfileResponse)
async def analyze_wallet(wallet_address:str,request:Request,limit:int=Query(default=DEFAULT_HISTORY_LIMIT,ge=1,le=MAX_HISTORY_LIMIT,description='Number of recent transactions to analyze.')):
 check_rate_limit(request);wallet_address=validate_wallet_address(wallet_address);_metrics['wallet_analysis_requests']+=1;cached=get_cached_wallet_profile(wallet_address,limit)
 if cached is not None:
  _metrics['cache_hits']+=1;_metrics['wallet_analysis_success']+=1;r=build_profile_summary(cached);r['cache']={'status':'HIT','ttl_seconds':CACHE_TTL_SECONDS,'history_limit':limit};return r
 _metrics['cache_misses']+=1;start=time.perf_counter()
 try:
  profile=await asyncio.wait_for(build_wallet_profile(wallet_address,limit=limit),timeout=ANALYSIS_TIMEOUT_SECONDS);_metrics['wallet_analysis_time_ms']+=(time.perf_counter()-start)*1000;_metrics['wallet_analysis_success']+=1;cache_wallet_profile(wallet_address,profile,limit);r=build_profile_summary(profile);r['cache']={'status':'MISS','ttl_seconds':CACHE_TTL_SECONDS,'history_limit':limit};return r
 except asyncio.TimeoutError:
  _metrics['wallet_analysis_timeouts']+=1;_metrics['wallet_analysis_errors']+=1;_metrics['wallet_analysis_time_ms']+=(time.perf_counter()-start)*1000;raise HTTPException(status_code=504,detail={'message':'Wallet analysis timed out. Please try again later.'})
 except ValueError:
  _metrics['wallet_analysis_errors']+=1;raise HTTPException(status_code=400,detail={'message':'Unable to process the wallet address.'})
 except Exception:
  _metrics['wallet_analysis_errors']+=1;logger.exception('Wallet analysis failed for wallet=%s limit=%s',wallet_address,limit);raise HTTPException(status_code=500,detail={'message':'Wallet analysis failed. Please try again later.'})
@app.get('/compare/{wallet_a}/{wallet_b}',tags=['Wallet Intelligence'],summary='Compare two Solana wallets',response_model=WalletComparisonResponse)
async def compare_wallets(wallet_a:str,wallet_b:str,request:Request,limit:int=Query(default=DEFAULT_HISTORY_LIMIT,ge=1,le=MAX_HISTORY_LIMIT,description='Number of recent transactions to analyze for each wallet.')):
 check_rate_limit(request);wallet_a=validate_wallet_address(wallet_a);wallet_b=validate_wallet_address(wallet_b)
 if wallet_a==wallet_b:raise HTTPException(status_code=400,detail={'message':'Wallet A and Wallet B must be different addresses.'})
 _metrics['comparison_requests']+=1
 try:
  profiles=await asyncio.wait_for(asyncio.gather(_analyze_for_compare(wallet_a,limit),_analyze_for_compare(wallet_b,limit)),timeout=ANALYSIS_TIMEOUT_SECONDS);result=compare_wallet_profiles(build_profile_summary(profiles[0]),build_profile_summary(profiles[1]));result['history_limit']=limit;result['generated_at']=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat();_metrics['comparison_success']+=1;return result
 except asyncio.TimeoutError: _metrics['comparison_errors']+=1;raise HTTPException(status_code=504,detail={'message':'Wallet comparison timed out. Please try again later.'})
 except ValueError: _metrics['comparison_errors']+=1;raise HTTPException(status_code=400,detail={'message':'Unable to process the wallet addresses.'})
 except Exception: _metrics['comparison_errors']+=1;logger.exception('Wallet comparison failed');raise HTTPException(status_code=500,detail={'message':'Wallet comparison failed. Please try again later.'})
@app.get('/discover/{seed_wallet}',tags=['Smart Wallet Discovery'],summary='Discover smart-wallet candidates',response_model=WalletDiscoveryResponse)
async def discover_wallets(seed_wallet:str,request:Request,history:int=Query(default=10,ge=1,le=50,description='Recent seed-wallet transactions to scan.'),candidates:int=Query(default=5,ge=1,le=10,description='Maximum candidates to return.'),candidate_history:int=Query(default=10,ge=1,le=20,description='Recent transactions used to score each candidate.')):
 check_rate_limit(request);seed_wallet=validate_wallet_address(seed_wallet);_metrics['discovery_requests']+=1
 try:
  result=await asyncio.wait_for(discover_smart_wallets(seed_wallet,history,candidates,candidate_history),timeout=ANALYSIS_TIMEOUT_SECONDS);_metrics['discovery_success']+=1;return result
 except asyncio.TimeoutError:_metrics['discovery_errors']+=1;raise HTTPException(status_code=504,detail={'message':'Wallet discovery timed out. Please try again later.'})
 except ValueError:_metrics['discovery_errors']+=1;raise HTTPException(status_code=400,detail={'message':'Unable to process the seed wallet.'})
 except Exception:_metrics['discovery_errors']+=1;logger.exception('Wallet discovery failed for seed_wallet=%s',seed_wallet);raise HTTPException(status_code=500,detail={'message':'Wallet discovery failed. Please try again later.'})
@app.get('/rank/{seed_wallet}',tags=['Smart Money Ranking'],summary='Rank discovered wallets by smart-money quality')
async def rank_wallets(seed_wallet:str,request:Request,history:int=Query(default=10,ge=1,le=50,description='Recent seed-wallet transactions to scan.'),candidates:int=Query(default=10,ge=1,le=10,description='Maximum candidate wallets to rank.'),candidate_history:int=Query(default=10,ge=1,le=20,description='Recent transactions used to score each candidate.'),min_confidence:float=Query(default=40,ge=0,le=100,description='Minimum data-confidence score required for ranking.')):
 check_rate_limit(request);seed_wallet=validate_wallet_address(seed_wallet);_metrics['ranking_requests']+=1
 try:
  discovered=await asyncio.wait_for(discover_smart_wallets(seed_wallet,history,candidates,candidate_history),timeout=ANALYSIS_TIMEOUT_SECONDS);ranked=rank_smart_wallets(discovered.get('candidates',[]),min_confidence=min_confidence);_metrics['ranking_success']+=1;return {'seed_wallet':seed_wallet,'history_scanned':discovered.get('history_scanned',0),'ranked_wallets':ranked,'ranking':{'method':'Confidence-adjusted smart-money ranking','minimum_confidence':min_confidence,'candidate_count':len(ranked),'read_only':True}}
 except asyncio.TimeoutError:_metrics['ranking_errors']+=1;raise HTTPException(status_code=504,detail={'message':'Smart-money ranking timed out. Please try again later.'})
 except ValueError:_metrics['ranking_errors']+=1;raise HTTPException(status_code=400,detail={'message':'Unable to process the seed wallet.'})
 except Exception:_metrics['ranking_errors']+=1;logger.exception('Smart-money ranking failed for seed_wallet=%s',seed_wallet);raise HTTPException(status_code=500,detail={'message':'Smart-money ranking failed. Please try again later.'})
if __name__=='__main__':
 import uvicorn;uvicorn.run('api:app',host=os.getenv('API_HOST','127.0.0.1'),port=int(os.getenv('API_PORT','8000')),reload=False)