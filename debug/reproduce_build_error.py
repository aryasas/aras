from flask import Flask, render_template

app = Flask(__name__, template_folder='../templates')

@app.route('/')
def test_render():
    try:
        # Pass the missing variable
        html = render_template('admin/setting/setting_dev_standalone.html', 
                               partial_template='admin/setting/setting_dev.html',
                               routes=[], modules=[], main_title="Test")
        print("Successfully rendered setting_dev_standalone.html")
        return html
    except Exception as e:
        print(f"Failed to render setting_dev_standalone.html: {e}")
        return str(e)

if __name__ == "__main__":
    with app.app_context():
        test_render()
