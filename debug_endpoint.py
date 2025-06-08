@app.get("/debug")
async def debug_info():
    import os
    return {
        "files": os.listdir("."),
        "current_time": datetime.utcnow().isoformat(),
        "environment": os.environ.get("RAILWAY_ENVIRONMENT"),
        "git_commit": os.environ.get("RAILWAY_GIT_COMMIT_SHA", "unknown")
    }
