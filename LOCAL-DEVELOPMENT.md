# Robot Puzzle Game - Local Development

This guide explains how to run and test the Robot Puzzle Game locally with the exact same behavior as the AWS deployment.

## 🚀 Quick Start

1. **Start the local server:**
   ```bash
   python3 local-server.py
   ```

2. **Open your browser to:**
   - **Game**: http://localhost:8000/
   - **Board Editor**: http://localhost:8000/wall-editor.html

## 🔧 Local Development Features

### ✅ **What Works Exactly Like AWS**
- ✅ Complete leaderboard system with rankings
- ✅ Round-based gameplay with baseline vs user-submitted boards
- ✅ Personal best tracking and score submission
- ✅ Board configuration tool with save/load
- ✅ Move history recording (stored but not displayed)
- ✅ All UI components: modals, selectors, completion screens
- ✅ mlusby@gmail.com baseline configuration behavior
- ✅ User-submitted boards only available when solved

### 🔄 **Local Differences**
- 🔄 No authentication required (auto-signed in as mlusby@gmail.com)
- 🔄 Data stored in browser localStorage instead of DynamoDB
- 🔄 Mock data pre-populated for immediate testing
- 🔄 Development banner shows local mode

## 📊 **Pre-populated Test Data**

The local environment includes sample data for testing:

### **Sample Rounds Available**
- **2 Baseline Rounds**: Authored by mlusby@gmail.com, available to all users
- **Various robot starting positions** and target configurations
- **Realistic board layouts** with walls and obstacles

### **Mock User Profile**
- **Email**: mlusby@gmail.com (baseline configuration author)
- **User ID**: local-user-123
- **Permissions**: Can create baseline configurations for all users

## 🎮 **Testing Scenarios**

### **1. Leaderboard Testing**
```bash
# Test complete leaderboard flow:
1. Start game → New Round → Complete puzzle
2. Submit score → View leaderboard
3. Try to beat your score → See "Score not improved" 
4. Complete different round → Compare rankings
```

### **2. Board Type Testing**
```bash
# Test board selector:
1. Select "Base Configurations" → Get mlusby@gmail.com boards
2. Select "User Submitted" → Get solved user configurations
3. Create new configuration → Solve it → See it in User Submitted
```

### **3. Configuration Tool Testing**
```bash
# Test board creation:
1. Open Board Editor → http://localhost:8000/wall-editor.html
2. Use Wall Tool → Click edges to add walls
3. Use Target Tool → Click centers to add targets
4. Save configuration → Return to game → Find it in User Submitted (after solving)
```

### **4. Score Persistence Testing**
```bash
# Test data persistence:
1. Complete rounds → Check localStorage for scores
2. Refresh browser → Verify personal bests persist
3. Clear localStorage → See fresh sample data reload
```

## 💾 **Local Data Storage**

All data is stored in browser localStorage with these keys:

```javascript
// View stored data in browser console:
localStorage.getItem('local-rounds')          // Available rounds
localStorage.getItem('local-configurations')  // Board configurations  
localStorage.getItem('local-scores')         // User scores and leaderboards
```

### **Reset Data**
```javascript
// Clear all local data and reload:
localStorage.clear();
location.reload();
```

## 🔍 **Debugging and Development**

### **Browser Console Commands**
```javascript
// Check current game state
window.game                    // Access game instance
window.authService.mockUser    // View mock user profile
window.apiService.isLocalDev   // Confirm local mode

// View stored data
Object.keys(localStorage)      // See all stored keys
JSON.parse(localStorage.getItem('local-scores'))  // View scores
```

### **Network Monitoring**
- 🚫 No actual network requests (all mocked)
- ✅ All API calls intercepted by local-dev.js
- ✅ Same response format as AWS Lambda functions

## 📁 **File Structure**

```
robots/
├── index-local.html           # Local development game page
├── wall-editor-local.html     # Local development board editor
├── local-server.py            # Development server
├── js/local-dev.js           # Mock AWS services
├── LOCAL-DEVELOPMENT.md       # This guide
└── [all other original files] # Unchanged production files
```

## 🆚 **Local vs AWS Comparison**

| Feature | Local Development | AWS Production |
|---------|------------------|----------------|
| Authentication | Auto-signed in | Cognito User Pools |
| Data Storage | localStorage | DynamoDB |
| API Calls | Mocked in JS | Lambda Functions |
| User Management | Single mock user | Real user accounts |
| Leaderboards | Local simulation | Global rankings |
| Board Sharing | Local only | Cross-user sharing |

## 🚨 **Common Issues**

### **Port 8000 Already in Use**
```bash
# Find and kill process using port 8000:
lsof -ti:8000 | xargs kill

# Or use a different port:
python3 -m http.server 8080
# Then visit: http://localhost:8080/
```

### **Browser Cache Issues**
```bash
# Force refresh with:
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)

# Or clear browser cache for localhost
```

### **Data Not Persisting**
- Check if browser allows localStorage for localhost
- Try different browser (Chrome, Firefox, Safari)
- Check browser's privacy/security settings

## 🎯 **Testing Checklist**

Use this checklist to verify all features work correctly:

- [ ] Game loads with development banner
- [ ] Board type selector shows baseline/user-submitted options
- [ ] New Round button loads different configurations
- [ ] Robots slide correctly until hitting walls/robots
- [ ] Move counter increments with each move
- [ ] Target robot reaching goal triggers completion modal
- [ ] Score submission shows success/improvement messages
- [ ] Leaderboard displays scores with rankings
- [ ] Personal best updates and persists
- [ ] Board editor opens and functions correctly
- [ ] Wall tool adds/removes walls on edge clicks
- [ ] Target tool adds/removes targets on center clicks
- [ ] Save configuration works and appears in game
- [ ] Delete configuration removes from list
- [ ] All modals open/close properly
- [ ] Responsive design works on mobile

## 💡 **Development Tips**

1. **Fast Testing**: Use browser dev tools to modify localStorage directly
2. **Mock Different Users**: Change `mockUser.email` in local-dev.js
3. **Add Test Data**: Modify `createSampleData()` function for specific scenarios
4. **Debug API Calls**: Add console.log statements in local-dev.js methods
5. **Test Edge Cases**: Clear localStorage and test with empty state

---

Happy coding! 🎮 This local setup gives you the exact same experience as the AWS deployment for rapid development and testing.