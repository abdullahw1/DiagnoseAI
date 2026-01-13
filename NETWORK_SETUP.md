# DiagnoseAI - Network Access Setup

This guide shows you how to make DiagnoseAI accessible to other devices on your local network (like your dad's phone/computer).

## 🚀 Quick Start

1. **Start the network server:**
   ```bash
   cd /Users/abdullahwaheed/Downloads/radiology-ai-application/DiagnoseAI
   source venv/bin/activate
   python run_network.py
   ```

2. **Share the URL:**
   - The script will show you the network URL (something like `http://192.168.1.100:5003`)
   - Share this URL with your dad
   - He can access it from any device on the same WiFi network

3. **Login:**
   - Username: `admin`
   - Password: `admin123`

## 📱 Access from Other Devices

Your dad can access DiagnoseAI from:
- **iPhone/Android**: Open Safari/Chrome and go to the network URL
- **iPad/Tablet**: Same as phone
- **Computer**: Any web browser with the network URL
- **Smart TV**: If it has a web browser

## 🔧 Network Requirements

**Same WiFi Network:**
- Your Mac and the accessing device must be on the same WiFi network
- Works with home WiFi, office networks, etc.
- Does NOT work over the internet (local network only)

**Firewall Settings:**
If your dad can't access it, you might need to allow the connection:

### macOS Firewall (if needed):
1. Go to System Preferences → Security & Privacy → Firewall
2. Click "Firewall Options"
3. Make sure "Block all incoming connections" is OFF
4. Or add Python to the allowed apps list

## 🔒 Security Considerations

**Safe for Local Use:**
- ✅ Only accessible on your local network
- ✅ Not exposed to the internet
- ✅ HTTP is fine for local network use
- ✅ No port forwarding or router configuration needed

**Security Best Practices:**
- Change the admin password after first login
- Only share the URL with trusted people
- Stop the server when not in use
- Don't use this setup on public WiFi

## 📋 Troubleshooting

### "Can't connect" or "Site not reachable"

1. **Check same network:**
   ```bash
   # On your Mac, check your IP:
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # Make sure other device shows similar IP range
   ```

2. **Check firewall:**
   - Temporarily disable Mac firewall to test
   - Add Python to firewall exceptions if needed

3. **Try different port:**
   - Edit `run_network.py` and change `port = 5003` to `port = 8080`
   - Some networks block certain ports

### "Server won't start"

1. **Port already in use:**
   ```bash
   # Kill any process using port 5003:
   lsof -ti:5003 | xargs kill -9
   ```

2. **Database issues:**
   ```bash
   # Reset database if needed:
   source venv/bin/activate
   flask db upgrade
   python create_admin_user.py
   ```

## 🎯 Usage Examples

### For Your Dad:
1. **Testing AI Analysis:**
   - Go to "AI Testing" in the menu
   - Upload ultrasound images
   - View AI analysis results
   - Rate the AI's performance

2. **Viewing Results:**
   - Click "AI Testing" → "Test Results"
   - Browse all previous tests
   - View detailed analysis with images

3. **Managing Tests:**
   - Evaluate AI performance with star ratings
   - Add comments about accuracy
   - Delete unwanted test results

## 🔄 Starting and Stopping

### Start Server:
```bash
cd /Users/abdullahwaheed/Downloads/radiology-ai-application/DiagnoseAI
source venv/bin/activate
python run_network.py
```

### Stop Server:
- Press `Ctrl+C` in the terminal
- Or close the terminal window

### Auto-start (Optional):
You can create a simple script to start it automatically:

```bash
# Create a desktop shortcut or alias
echo 'cd /Users/abdullahwaheed/Downloads/radiology-ai-application/DiagnoseAI && source venv/bin/activate && python run_network.py' > ~/Desktop/start_diagnoseai.sh
chmod +x ~/Desktop/start_diagnoseai.sh
```

## 📞 Support

**Common Issues:**
- **Can't access from phone**: Check both devices are on same WiFi
- **Slow loading**: Normal for AI analysis, can take 30-60 seconds
- **Login issues**: Use `admin` / `admin123`, case-sensitive
- **Upload fails**: Check image format (JPG, PNG supported)

**Getting Help:**
- Check the terminal output for error messages
- Try accessing locally first: `http://127.0.0.1:5003`
- Restart the server if issues persist

## 🎉 Features Available

Once connected, your dad can:
- ✅ Upload and analyze ultrasound images
- ✅ View AI-generated reports
- ✅ Rate AI performance
- ✅ Browse test history with images
- ✅ Export results
- ✅ Manage test data

Perfect for testing the AI's accuracy on your liver pathology images!