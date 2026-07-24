from fastapi import FastAPI,Request
app=FastAPI()
@app.api_route("/{path:path}",methods=["GET","POST","PUT","DELETE"])
async def echo(path:str,request:Request):
    return {
        "upstream":"mock",
        "method":request.method,
        "path":f"/{path}",
        "status":"ok",
    }