from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from PIL import Image
from pyzbar.pyzbar import decode
from werkzeug.security import check_password_hash
import os, re, requests
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Supabase configuration - using your direct credentials
SUPABASE_URL = 'https://ffcdoxneybkdmeeokddy.supabase.co'
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or "your-supabase-key-here"  # Make sure to set this in your .env file

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

# Production error handling
if os.getenv('FLASK_ENV') == 'production':
    import logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    
    # Error handlers for production
    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f"Server Error: {error}")
        return "Internal Server Error", 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        return "Page Not Found", 404

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat-v3.1:free"

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if response.data and len(response.data) > 0:
            user_data = response.data[0]
            return User(user_data['id'], user_data['username'], user_data['role'])
        return None
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

def create_default_user():
    """Create a default admin user if none exists"""
    try:
        # Check if any users exist
        response = supabase.table('users').select('*').execute()
        
        if len(response.data) == 0:
            # Create default admin user
            supabase.table('users').insert({
                'username': 'admin',
                'password': 'admin123',
                'role': 'admin'
            }).execute()
            # Create default regular user
            supabase.table('users').insert({
                'username': 'user',
                'password': 'user123',
                'role': 'user'
            }).execute()
            print("✅ Default users created: admin/admin123, user/user123")
    except Exception as e:
        print(f"User creation error: {e}")

def init_database():
    """Initialize database tables if they don't exist"""
    try:
        # Note: With Supabase, you'll need to create tables through the Supabase dashboard
        # or using SQL in the Supabase SQL editor. Tables are not created programmatically.
        print("ℹ️  Ensure tables exist in Supabase: users, track_fittings, replacement_reports")
    except Exception as e:
        print(f"Database initialization error: {e}")

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect("/admin-dashboard" if current_user.role == "admin" else "/user-dashboard")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            response = supabase.table('users').select('*').eq('username', username).execute()
            if response.data and len(response.data) > 0:
                user = response.data[0]
                if password == user['password']:  # Simple password check
                    login_user(User(user['id'], user['username'], user['role']))
                    return redirect("/")
            return "❌ Invalid credentials"
        except Exception as e:
            return f"❌ Login error: {e}"
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/admin-dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return "⛔ Access denied"
    return render_template("admin_dashboard.html")

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if current_user.role != "admin":
        return "⛔ Access denied"
    try:
        query = supabase.table('track_fittings').select('*')
        
        if request.method == "POST":
            vendor = request.form.get("vendor")
            status = request.form.get("inspection_status")
            
            if vendor:
                query = query.eq('vendor', vendor)
            if status:
                query = query.eq('inspection_status', status)
        
        response = query.execute()
        records = response.data
        return render_template("dashboard.html", records=records)
    except Exception as e:
        return f"❌ Database error: {e}"

@app.route("/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    if current_user.role != "admin":
        return "⛔ Access denied"
    try:
        if request.method == "POST":
            data = {
                'item': request.form["item"],
                'vendor': request.form["vendor"],
                'lot': request.form["lot"],
                'supply_date': request.form["supply_date"],
                'warranty': request.form["warranty"],
                'inspection_status': request.form["inspection_status"],
                'location': request.form["location"]
            }
            supabase.table('track_fittings').update(data).eq('id', entry_id).execute()
            return "✅ Entry updated. <a href='/dashboard'>Go back</a>"
        
        response = supabase.table('track_fittings').select('*').eq('id', entry_id).execute()
        record = response.data[0] if response.data else None
        return render_template("edit_entry.html", record=record)
    except Exception as e:
        return f"❌ Error: {e}"

@app.route("/export")
@login_required
def export_csv():
    if current_user.role != "admin":
        return "⛔ Access denied"
    try:
        response = supabase.table('track_fittings').select('*').execute()
        rows = response.data
        
        def generate():
            yield "ID,Item,Vendor,Lot,Supply Date,Warranty,Inspection,Location\n"
            for row in rows:
                yield f"{row['id']},{row['item']},{row['vendor']},{row['lot']},{row['supply_date']},{row['warranty']},{row['inspection_status']},{row['location']}\n"
        
        return Response(generate(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=qr_metadata.csv"})
    except Exception as e:
        return f"❌ Export error: {e}"

@app.route("/user-dashboard")
@login_required
def user_dashboard():
    if current_user.role != "user":
        return "⛔ Access denied"
    return redirect("/user-scan-upload")

@app.route("/user-scan-upload", methods=["GET", "POST"])
@login_required
def user_scan_upload():
    if current_user.role != "user":
        return "⛔ Access denied"
    return render_template("user_scan_upload.html")

@app.route("/upload-qr", methods=["POST"])
@login_required
def upload_qr():
    if current_user.role != "user":
        return "⛔ Access denied"
    if 'qr_image' not in request.files:
        return "❌ No file uploaded"
    
    file = request.files["qr_image"]
    if file.filename == '':
        return "❌ No file selected"
    
    try:
        img = Image.open(file.stream)
        decoded = decode(img)
        if decoded:
            qr_data = decoded[0].data.decode("utf-8")
            return redirect(f"/view-details?code={qr_data}")
        return "❌ QR code not detected."
    except Exception as e:
        return f"❌ Error processing image: {e}"

def parse_warranty(warranty_str):
    if not warranty_str:
        return 0
    match = re.match(r"(\d+)\s*(year|month|day)s?", warranty_str.lower())
    if not match:
        return 0
    value, unit = match.groups()
    value = int(value)
    return value * 365 if unit == "year" else value * 30 if unit == "month" else value

@app.route("/view-details")
@login_required
def view_details():
    if current_user.role != "user":
        return "⛔ Access denied"
    qr_code = request.args.get("code")
    if not qr_code:
        return "❌ No QR code provided"
    
    try:
        response = supabase.table('track_fittings').select('*').eq('lot', qr_code).execute()
        if not response.data or len(response.data) == 0:
            return "❌ No matching record found."
        
        record = response.data[0]
        item = record['item']
        vendor = record['vendor']
        lot = record['lot']
        supply_date = record['supply_date']
        warranty = record['warranty']
        status = record['inspection_status']
        location = record['location']
        
        # Handle date parsing
        if isinstance(supply_date, str):
            supply_date = datetime.strptime(supply_date, "%Y-%m-%d")
        
        warranty_days = parse_warranty(warranty)
        warranty_end = supply_date + timedelta(days=warranty_days)
        today = datetime.now().date()
        
        warranty_status = f"✅ Warranty valid until {warranty_end.date()} ({(warranty_end.date() - today).days} days left)" if today <= warranty_end.date() else f"❌ Warranty expired on {warranty_end.date()} ({(today - warranty_end.date()).days} days ago)"
        
        # Skip AI message processing for faster loading
        ai_message = None

        replacement_report = None
        if today > warranty_end.date():
            agentic_prompt = f"""
            The following railway fitting has expired warranty. Generate a replacement report.

            Product: {item}
            Vendor: {vendor}
            Lot: {lot}
            Supply Date: {supply_date.date()}
            Warranty: {warranty}
            Expired On: {warranty_end.date()}
            Inspection Status: {status}
            Location: {location}

            Please generate a professional replacement report explaining the situation and recommending next steps.
            """

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "AI-Driven QR Code System"
            }

            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant for warranty validation and railway fittings inspection."},
                    {"role": "user", "content": agentic_prompt}
                ],
                "max_tokens": 300,
                "temperature": 0.3
            }

            payload["messages"][1]["content"] = agentic_prompt
            try:
                response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
                data = response.json()
                replacement_report = data["choices"][0]["message"]["content"]
            except Exception as e:
                replacement_report = f"⚠️ Could not generate replacement report: {e}"

            # Save replacement report to database
            try:
                supabase.table('replacement_reports').insert({
                    'lot': lot,
                    'item': item,
                    'vendor': vendor,
                    'expired_on': warranty_end.date().isoformat(),
                    'report': replacement_report
                }).execute()
            except Exception as e:
                print(f"Error saving replacement report: {e}")

        return render_template(
            "view_details.html",
            record=record,
            ai_message=ai_message,
            warranty_status=warranty_status,
            replacement_report=replacement_report
        )
    except Exception as e:
        return f"❌ Error: {e}"

@app.route("/agent-query", methods=["POST"])
@login_required
def agent_query():
    if current_user.role != "admin":
        return jsonify({"error": "⛔ Access denied"})

    user_query = request.json.get("query") if request.json else None
    if not user_query:
        return jsonify({"error": "No query provided"})
    
    try:
        # Process AI query using OpenRouter API
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "AI-Driven QR Code System"
        }

        # Get database context for the AI
        try:
            response = supabase.table('track_fittings').select('*').execute()
            records = response.data
            
            # Create context summary
            total_items = len(records)
            pending_inspections = len([r for r in records if r.get('inspection_status') == 'Pending'])
            passed_inspections = len([r for r in records if r.get('inspection_status') == 'Passed'])
            failed_inspections = len([r for r in records if r.get('inspection_status') == 'Failed'])
            
            # Get recent items for context
            recent_items = records[:5] if records else []
            
            context = f"""Database Context:
- Total QR Items: {total_items}
- Pending Inspections: {pending_inspections}
- Passed Inspections: {passed_inspections}
- Failed Inspections: {failed_inspections}

Recent Items Sample:
"""
            
            for item in recent_items:
                context += f"- {item.get('item', 'N/A')} | Vendor: {item.get('vendor', 'N/A')} | Status: {item.get('inspection_status', 'N/A')} | Lot: {item.get('lot', 'N/A')}\n"
                
        except Exception as e:
            context = f"Database connection error: {e}"

        # Create AI prompt
        system_prompt = """You are an AI assistant for a railway fittings inspection system. You help analyze QR code metadata, inspection status, warranty information, and provide insights about railway track fittings.

Your capabilities:
- Analyze inspection data and provide recommendations
- Explain warranty status and maintenance schedules
- Identify potential issues with railway fittings
- Generate reports and summaries
- Answer questions about track fitting specifications

Provide helpful, accurate, and actionable responses related to railway maintenance and inspection."""

        user_prompt = f"""{context}

User Query: {user_query}

Please provide a helpful response based on the railway fittings data and context above."""

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }

        try:
            ai_response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
            ai_data = ai_response.json()
            
            if "choices" in ai_data and len(ai_data["choices"]) > 0:
                ai_message = ai_data["choices"][0]["message"]["content"]
                return jsonify({"response": ai_message, "success": True})
            else:
                return jsonify({"error": "⚠️ Unexpected AI response format"})
                
        except Exception as e:
            return jsonify({"error": f"⚠️ Error contacting AI service: {str(e)}"})
            
    except Exception as e:
        print(f"Agent query error: {e}")
        return jsonify({"error": f"Query failed: {str(e)}"})
@app.route("/ai-report")
@login_required
def ai_report():
    if current_user.role != "admin":
        return "⛔ Access denied"
    try:
        # Generate an AI-powered inspection report
        response = supabase.table('track_fittings').select('*').execute()
        records = response.data
        
        if not records:
            report_content = "No track fitting records found in the database. Please add some QR data first."
        else:
            # Generate summary report
            total_items = len(records)
            pending_inspections = len([r for r in records if r.get('inspection_status') == 'Pending'])
            passed_inspections = len([r for r in records if r.get('inspection_status') == 'Passed'])
            failed_inspections = len([r for r in records if r.get('inspection_status') == 'Failed'])
            
            # Check for expired warranties
            today = datetime.now().date()
            expired_items = []
            for record in records:
                try:
                    supply_date = record.get('supply_date')
                    if isinstance(supply_date, str):
                        supply_date = datetime.strptime(supply_date, "%Y-%m-%d").date()
                    elif hasattr(supply_date, 'date'):
                        supply_date = supply_date.date()
                    
                    warranty = record.get('warranty', '')
                    warranty_days = parse_warranty(warranty)
                    if warranty_days > 0:
                        warranty_end = supply_date + timedelta(days=warranty_days)
                        if today > warranty_end:
                            expired_items.append({
                                'lot': record.get('lot'),
                                'item': record.get('item'),
                                'expired_days': (today - warranty_end).days
                            })
                except:
                    continue
            
            # Create comprehensive report
            report_content = f"""🤖 AI-POWERED RAILWAY FITTINGS INSPECTION REPORT
{'='*60}

📊 SUMMARY STATISTICS:
• Total QR Items in Database: {total_items}
• Pending Inspections: {pending_inspections}
• Passed Inspections: {passed_inspections} 
• Failed Inspections: {failed_inspections}
• Items with Expired Warranty: {len(expired_items)}

⚠️ WARRANTY STATUS ANALYSIS:"""
            
            if expired_items:
                report_content += "\n\n🔴 EXPIRED WARRANTY ITEMS (Immediate Action Required):\n"
                for item in expired_items[:10]:  # Limit to 10 items
                    report_content += f"• Lot: {item['lot']} | Item: {item['item']} | Expired: {item['expired_days']} days ago\n"
                if len(expired_items) > 10:
                    report_content += f"... and {len(expired_items) - 10} more items\n"
            else:
                report_content += "\n\n✅ All items are within warranty period.\n"
            
            # Add inspection recommendations
            report_content += f"\n\n🔍 INSPECTION RECOMMENDATIONS:\n"
            if pending_inspections > 0:
                report_content += f"• Priority: Complete {pending_inspections} pending inspections\n"
            if failed_inspections > 0:
                report_content += f"• Critical: Review and replace {failed_inspections} failed items\n"
            if len(expired_items) > 0:
                report_content += f"• Urgent: Process replacement for {len(expired_items)} expired items\n"
            
            report_content += f"\n\n📈 SYSTEM HEALTH SCORE: {((passed_inspections + pending_inspections) / max(total_items, 1) * 100):.1f}%\n"
            report_content += f"\n📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report_content += "\n" + "="*60
        
        return render_template("ai_report.html", report=report_content)
    except Exception as e:
        return f"❌ Error generating AI report: {e}"

@app.route("/ai-report/export")
@login_required
def export_ai_report():
    if current_user.role != "admin":
        return "⛔ Access denied"
    try:
        # Generate the same report content as above
        response = supabase.table('track_fittings').select('*').execute()
        records = response.data
        
        def generate():
            yield "Railway Fittings AI Inspection Report\n"
            yield f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            if not records:
                yield "No track fitting records found in the database.\n"
            else:
                total_items = len(records)
                pending_inspections = len([r for r in records if r.get('inspection_status') == 'Pending'])
                passed_inspections = len([r for r in records if r.get('inspection_status') == 'Passed'])
                failed_inspections = len([r for r in records if r.get('inspection_status') == 'Failed'])
                
                yield f"Total Items: {total_items}\n"
                yield f"Pending Inspections: {pending_inspections}\n"
                yield f"Passed Inspections: {passed_inspections}\n"
                yield f"Failed Inspections: {failed_inspections}\n\n"
                
                # Export expired items
                today = datetime.now().date()
                yield "Expired Warranty Items:\n"
                yield "Lot,Item,Vendor,Supply Date,Warranty,Expired Days\n"
                
                for record in records:
                    try:
                        supply_date = record.get('supply_date')
                        if isinstance(supply_date, str):
                            supply_date = datetime.strptime(supply_date, "%Y-%m-%d").date()
                        elif hasattr(supply_date, 'date'):
                            supply_date = supply_date.date()
                        
                        warranty = record.get('warranty', '')
                        warranty_days = parse_warranty(warranty)
                        if warranty_days > 0:
                            warranty_end = supply_date + timedelta(days=warranty_days)
                            if today > warranty_end:
                                expired_days = (today - warranty_end).days
                                yield f"{record.get('lot', '')},{record.get('item', '')},{record.get('vendor', '')},{supply_date},{warranty},{expired_days}\n"
                    except:
                        continue
        
        return Response(generate(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=ai_inspection_report.csv"})
    except Exception as e:
        return f"❌ Export error: {e}"

@app.route("/ai-chat")
@login_required
def ai_chat():
    if current_user.role != "admin":
        return "⛔ Access denied"
    return render_template("ai_chat.html")

@app.route("/admin-reports")
@login_required
def admin_reports():
    if current_user.role != "admin":
        return "⛔ Access denied"
    try:
        response = supabase.table('replacement_reports').select('*').order('created_at', desc=True).execute()
        reports = response.data
        return render_template("admin_report.html", reports=reports)
    except Exception as e:
        return f"❌ Error loading reports: {e}"

@app.route("/generate-report", methods=["POST"])
@login_required
def generate_report():
    if current_user.role != "user":
        return "⛔ Access denied"

    lot = request.form.get("lot")
    if not lot:
        return "❌ No lot number provided"
    
    try:
        response = supabase.table('track_fittings').select('*').eq('lot', lot).execute()
        if not response.data or len(response.data) == 0:
            return "❌ No matching record found."

        record = response.data[0]
        item = record['item']
        vendor = record['vendor']
        lot = record['lot']
        supply_date = record['supply_date']
        warranty = record['warranty']
        status = record['inspection_status']
        location = record['location']
        
        # Handle date parsing
        if isinstance(supply_date, str):
            supply_date = datetime.strptime(supply_date, "%Y-%m-%d")
        
        warranty_days = parse_warranty(warranty)
        warranty_end = supply_date + timedelta(days=warranty_days)

        agentic_prompt = f"""
        Generate a replacement report for an expired railway fitting.

        Product: {item}
        Vendor: {vendor}
        Lot: {lot}
        Supply Date: {supply_date.date()}
        Warranty: {warranty}
        Expired On: {warranty_end.date()}
        Inspection Status: {status}
        Location: {location}

        Please explain the issue in simple terms and recommend next steps for replacement.
        Provide a professional report that can be used for procurement purposes.
        """

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "AI-Driven QR Code System"
        }

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are an assistant that generates replacement reports for expired railway products."},
                {"role": "user", "content": agentic_prompt}
            ],
            "max_tokens": 400,
            "temperature": 0.4
        }

        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
            data = response.json()
            replacement_report = data["choices"][0]["message"]["content"]
        except Exception as e:
            replacement_report = f"⚠️ Could not generate replacement report: {e}"

        # Save to database
        try:
            supabase.table('replacement_reports').insert({
                'lot': lot,
                'item': item,
                'vendor': vendor,
                'expired_on': warranty_end.date().isoformat(),
                'report': replacement_report
            }).execute()
        except Exception as e:
            print(f"Error saving report: {e}")

        return redirect("/admin-reports")
    except Exception as e:
        return f"❌ Error: {e}"

@app.route("/report-generated/<lot>")
@login_required
def report_generated(lot):
    if current_user.role != "user":
        return "⛔ Access denied"
    
    try:
        # Get the latest replacement report for this lot
        response = supabase.table('replacement_reports').select('*').eq('lot', lot).order('created_at', desc=True).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            report_data = response.data[0]
            return render_template("report_generated.html", 
                                lot=lot, 
                                report=report_data['report'])
        else:
            return "❌ No replacement report found for this lot."
    except Exception as e:
        return f"❌ Error loading report: {e}"

@app.route("/health")
def health_check():
    """Health check endpoint for Render"""
    try:
        # Test database connection
        response = supabase.table('users').select('*').limit(1).execute()
        db_status = "✅ Database connected"
        db_healthy = True
    except Exception as e:
        db_status = f"❌ Database error: {e}"
        db_healthy = False
    
    health_data = {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv('FLASK_ENV', 'development')
    }
    
    return jsonify(health_data), 200 if db_healthy else 503

if __name__ == "__main__":
    # Initialize database and create default users
    try:
        init_database()
        create_default_user()
    except Exception as e:
        print(f"Initialization warning: {e}")
    
    print("🚀 Starting Flask application...")
    print("📝 Default users: admin/admin123, user/user123")
    print(f"🔗 Supabase URL: {SUPABASE_URL}")
    
    # Use environment variable for port (Render requirement)
    port = int(os.environ.get('PORT', 5000))
    # Disable debug in production
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(host="0.0.0.0", port=port, debug=debug_mode)