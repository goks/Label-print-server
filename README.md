# Label Print Server

A simple Flask web app to lookup party name by quotation number and print a label via network printer on Windows.

## Setup

1. Install requirements:
   ```
   pip install -r requirements.txt
   ```

2. Configure database credentials in `app.py`.
3. Ensure the HPRT h300 printer is installed and set as the default printer on Windows.
4. Run the server:
   ```
   python app.py
   ```
5. Access from Raspberry Pi browser (replace `SERVER_IP`):
   ```
   http://SERVER_IP:5000/
   ```

## Usage

- Type the quotation number, see the party name.
- Press Enter or click "Print Label" to print.
- Each Enter prints another label.

---