from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run("0.0.0.0", port=8001, debug=False)