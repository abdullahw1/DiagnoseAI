# DiagnoseAI - Internet Access Setup

Since your dad is not on the same WiFi network, here are the easiest ways to make DiagnoseAI accessible over the internet.

## 🚀 Option 1: ngrok (Recommended - Easiest)

ngrok creates a secure tunnel from the internet to your Mac. It's free and takes 2 minutes to set up.

### Setup Steps:

1. **Install ngrok:**
   ```bash
   # Using Homebrew (easiest):
   brew install ngrok/ngrok/ngrok
   
   # Or download from: https://ngrok.com/download
   ```

2. **Sign up for free account:**
   - Go to https://ngrok.com/signup
   - Get your auth token from the dashboard

3. **Configure ngrok:**
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
   ```

4. **Start DiagnoseAI with internet access:**
   ```bash
   cd /Users/abdullahwaheed/Downloads/radiology-ai-application/DiagnoseAI
   source venv/bin/activate
   python run_internet.py
   ```

5. **Share the URL:**
   - The script will show a public URL like: `https://abc123.ngrok.io`
   - Send this URL to your dad
   - He can access it from anywhere in the world!

### Benefits:
- ✅ Free (with some limitations)
- ✅ HTTPS automatically enabled
- ✅ Works from anywhere
- ✅ No router configuration needed
- ✅ Secure tunnel

### Limitations:
- URL changes each time you restart (free plan)
- 2-hour session limit (free plan)
- Can upgrade for permanent URLs

---

## 🚀 Option 2: Cloudflare Tunnel (Alternative)

Similar to ngrok but by Cloudflare. Also free and reliable.

### Setup Steps:

1. **Install cloudflared:**
   ```bash
   brew install cloudflare/cloudflare/cloudflared
   ```

2. **Start tunnel:**
   ```bash
   # First, start DiagnoseAI locally:
   cd /Users/abdullahwaheed/Downloads/radiology-ai-application/DiagnoseAI
   source venv/bin/activate
   python run_local.py
   
   # In another terminal, create tunnel:
   cloudflared tunnel --url http://localhost:5003
   ```

3. **Share the URL:**
   - Cloudflared will show a public URL
   - Send this to your dad

---

## 🚀 Option 3: Railway/Heroku (Cloud Deployment)

Deploy to a cloud service for permanent access.

### Railway (Easiest Cloud Option):

1. **Push to GitHub** (if not already done)
2. **Go to railway.app**
3. **Connect GitHub repo**
4. **Deploy automatically**
5. **Get permanent URL**

See `railway-deploy.md` for detailed instructions.

---

## 🔒 Security Considerations

### For Internet Access:
- ⚠️ Your app will be accessible from anywhere
- 🔑 Change the admin password immediately
- 🚫 Don't share the URL publicly
- 🛑 Stop the server when not in use

### Recommended Security Steps:
1. **Change default password:**
   - Login with admin/admin123
   - Change to a strong password
   
2. **Create separate user for your dad:**
   - Register a new account for him
   - Use his own username/password

3. **Monitor access:**
   - Check who's accessing the system
   - Stop the server when done testing

---

## 📱 Instructions for Your Dad

Once you have the public URL:

### Accessing DiagnoseAI:
1. **Open any web browser** (Chrome, Safari, Firefox, etc.)
2. **Go to the URL you provided** (e.g., https://abc123.ngrok.io)
3. **Login:**
   - Username: admin (or the account you created for him)
   - Password: admin123 (or the password you set)

### Using the AI Testing:
1. **Click "AI Testing"** in the menu
2. **Upload an ultrasound image** (JPG, PNG formats)
3. **Select view type** if known (Left Lobe TR, Portal Vein, etc.)
4. **Click "Analyze Image with AI"**
5. **Wait 30-60 seconds** for AI analysis
6. **Review the results** and rate the AI's performance

### Viewing Results:
1. **Click "AI Testing" → "Test Results"** to see all previous tests
2. **Click any result** to see detailed analysis with the image
3. **Rate the AI's performance** using the star system
4. **Add comments** about accuracy

---

## 🛠 Troubleshooting

### ngrok Issues:
```bash
# If ngrok fails, try manual setup:
# Terminal 1 - Start DiagnoseAI:
python run_local.py

# Terminal 2 - Start ngrok:
ngrok http 5003
```

### Connection Issues:
- Make sure your Mac doesn't go to sleep
- Check your internet connection
- Try restarting the tunnel if it stops working

### Performance Issues:
- AI analysis takes 30-60 seconds (normal)
- Large images may take longer to upload
- Internet speed affects upload/download times

---

## 💡 Quick Start Summary

**Fastest way to get your dad access:**

1. Install ngrok: `brew install ngrok/ngrok/ngrok`
2. Sign up at ngrok.com and get auth token
3. Configure: `ngrok config add-authtoken YOUR_TOKEN`
4. Run: `python run_internet.py`
5. Share the https URL with your dad
6. He logs in with admin/admin123

**Total setup time: ~5 minutes**

Your dad can then test all your liver pathology images and rate the AI's performance from anywhere in the world!