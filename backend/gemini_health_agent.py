        else:
            print("⚠️ WARNING: No GEMINI_API_KEY found. Using fallback responses.")
            self.use_gemini = False
        
        self.system_prompt = """
        You are a warm, caring, and friendly AI Health Companion. 
        Your goal is to support elderly users and their caregivers with understanding health data, offering reassurance, and being a helpful presence.
        
        PERSONA:
        - You are NOT a robot. You are a companion.
        - Speak naturally, like a caring friend or family member.
        - Be empathetic, patient, and encouraging.
        - Use the user's name to make the conversation personal.
        
        RULES:
        1. Use simple, kind, and clear language. Avoid overly technical jargon unless necessary, and explain it if you do.
        2. NEVER provide a medical diagnosis. You are a companion, not a doctor.
        3. If values seem dangerous (e.g., very high BP, low SpO2), gently but firmly suggest contacting a doctor immediately.
        4. Use the context provided to answer questions about heart rate, blood pressure, etc.
        5. Keep responses concise but warm.
        6. Use emojis to add warmth and emotion to your messages. 💙 🌿
        """

    def get_recent_vitals(self, username: str, limit: int = 5) -> str:
        """Tool to fetch recent vitals for a user."""
        db: Session = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return "User not found."
        
        vitals = db.query(Vital).filter(Vital.user_id == user.id).order_by(Vital.timestamp.desc()).limit(limit).all()
        
        if not vitals:
            return "No recent vitals found."
        
        report = []
        for v in vitals:
            status = "⚠️ Abnormal" if v.is_abnormal else "✅ Normal"
            report.append(f"- {v.timestamp.strftime('%Y-%m-%d %H:%M')}: {v.type} = {v.value} {v.unit} ({status})")
        
        return "\n".join(report)

    def chat(self, user_message: str, username: str) -> str:
        # 1. Gather Context (Simple RAG)
        # Fetch user details to get full name
        db: Session = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        full_name = user.full_name if user and user.full_name else username
        
        context = self.get_recent_vitals(username)
        
        # 2. Construct Prompt
        full_prompt = f"""
        {self.system_prompt}
        
        USER INFORMATION:
        Name: {full_name}
        
        CONTEXT (Recent Health Data):
        {context}
        
        USER QUESTION:
        {user_message}
        
        Please provide a helpful, friendly response. Address the user by their name occasionally to be more personal.
        """
        
        # 3. Call Gemini API or use fallback
        try:
            if self.use_gemini:
                print(f"🤖 Calling Gemini API for user: {username}")
                response = self.model.generate_content(full_prompt)
                print("✅ Gemini response received")
                return response.text
            else:
                # Fallback responses when no API key
                return self._fallback_response(user_message, context, full_name)
        except Exception as e:
            print(f"❌ Error calling Gemini: {e}")
            # Log error to file for debugging
            with open("gemini_error.log", "a") as f:
                f.write(f"{datetime.now()}: {str(e)}\n")
            return self._fallback_response(user_message, context, full_name)
    
    def _fallback_response(self, user_message: str, context: str, full_name: str) -> str:
        """Provide intelligent fallback responses without API."""
        msg_lower = user_message.lower()
        
        # Personalize greeting
        greeting_name = f" {full_name}" if full_name else ""
        
        # Check for "How are you"
        if 'how are you' in msg_lower:
            return f"I'm doing well, thank you for asking, {full_name}! I'm ready to help you with your health data. How are you feeling today? 💙"

        # Check if asking about name/identity
        if any(phrase in msg_lower for phrase in ['my name', 'who am i', 'know me']):
            return f"You are {full_name}! I'm here to help you stay healthy, {full_name}. 💙"
            
        if any(phrase in msg_lower for phrase in ['who are you', "who're you", "who'r you", "your name"]):
            return f"I am your AI Health Companion, {full_name}. I'm here to monitor your vitals and answer your health questions. 🤝"

        # Check for advice/improvement questions (Prioritize this over specific vitals)
        import random
        
        # 1. Blood Pressure specific management
        bp_keywords = ['blood pressure', 'bp', 'pressure']
        management_keywords = ['manage', 'control', 'controll', 'reduce', 'lower', 'improve', 'fix', 'how to', 'what do', 'what i do', 'normalize', 'maintain']
        
        if any(bp in msg_lower for bp in bp_keywords) and any(mgmt in msg_lower for mgmt in management_keywords):
            responses = [
                f"Managing blood pressure is very important, {full_name}. Here are some general tips: reduce salt intake, maintain a healthy weight, exercise regularly (like walking 30 minutes daily), limit alcohol, and manage stress. However, please discuss your specific readings with your doctor for personalized advice! 🩺",
                f"Good question about blood pressure control! Generally: eat more fruits and vegetables, reduce sodium, stay active, and avoid smoking. But since your readings show some abnormality, it's crucial to consult your doctor for a proper treatment plan. 💙",
                f"Blood pressure management typically involves lifestyle changes like eating less salt, exercising regularly, maintaining healthy weight, and reducing stress. Some people also need medication. Please talk to your doctor about the best approach for your specific situation! 🏥"
            ]
            return random.choice(responses)
        
        # 2. Heart Rate specific management
        hr_keywords = ['heart rate', 'heart', 'hr', 'pulse', 'heartbeat']
        
        if any(hr in msg_lower for hr in hr_keywords) and any(mgmt in msg_lower for mgmt in management_keywords):
            responses = [
                f"To maintain a healthy heart rate, {full_name}: stay physically active with regular cardio exercise, manage stress through relaxation techniques, get adequate sleep (7-9 hours), limit caffeine and alcohol, and stay hydrated. If your heart rate is consistently abnormal, please see your doctor! ❤️",
                f"Heart rate management involves regular exercise (which actually strengthens your heart over time), stress reduction, avoiding excessive caffeine, and maintaining good sleep habits. For persistent issues, your doctor might recommend specific treatments. 💓",
                f"Good question! A healthy heart rate comes from: regular physical activity, stress management, proper hydration, limiting stimulants like caffeine, and getting enough rest. Always consult your doctor if you notice irregular patterns! 🫀"
            ]
            return random.choice(responses)
        
        # 3. Glucose/Blood Sugar specific management
        glucose_keywords = ['glucose', 'sugar', 'blood sugar', 'diabetes']
        
        if any(gluc in msg_lower for gluc in glucose_keywords) and any(mgmt in msg_lower for mgmt in management_keywords):
            responses = [
                f"Managing blood glucose is crucial, {full_name}. Key strategies: eat balanced meals with complex carbs and fiber, exercise regularly, maintain healthy weight, monitor your levels as advised, limit sugary foods and drinks, and take medications as prescribed. Your doctor can create a personalized plan! 🩸",
                f"Blood sugar control involves: eating at regular intervals, choosing whole grains over refined carbs, including protein and healthy fats in meals, staying active, managing stress, and monitoring your levels. Please work with your doctor for specific targets! 📊",
                f"Great question about glucose management! Focus on: balanced diet with low glycemic foods, regular physical activity, weight management, stress reduction, and consistent meal timing. If you have diabetes, follow your doctor's medication and monitoring plan closely. 🍎"
            ]
            return random.choice(responses)
        
        # 4. SpO2/Oxygen specific management
        spo2_keywords = ['spo2', 'oxygen', 'o2', 'saturation']
        
        if any(spo2 in msg_lower for spo2 in spo2_keywords) and any(mgmt in msg_lower for mgmt in management_keywords):
            responses = [
                f"To maintain healthy oxygen levels, {full_name}: practice deep breathing exercises, stay physically active to strengthen lungs, maintain good posture, ensure good air quality in your home, and avoid smoking. If levels are consistently low, see your doctor immediately! 🫁",
                f"Oxygen saturation can be improved through: regular breathing exercises, cardiovascular exercise, maintaining healthy weight, good posture, and avoiding pollutants. Low SpO2 can be serious - always consult your doctor if readings are below 95%! 💨",
                f"Good question! Supporting healthy oxygen levels: do breathing exercises, stay active, keep airways clear, maintain good indoor air quality, and avoid smoking. Persistent low readings need immediate medical attention! 🌬️"
            ]
            return random.choice(responses)
        
        # 5. Temperature/Fever specific management
        temp_keywords = ['temperature', 'temp', 'fever']
        
        if any(temp in msg_lower for temp in temp_keywords) and any(mgmt in msg_lower for mgmt in management_keywords):
            responses = [
                f"For managing fever or temperature, {full_name}: stay hydrated, rest adequately, use cool compresses if needed, dress in light clothing, and monitor your temperature regularly. For fever above 100.4°F or lasting more than 3 days, contact your doctor! 🌡️",
                f"Temperature management tips: drink plenty of fluids, get rest, take fever-reducing medication if recommended by your doctor, use lukewarm baths (not cold), and monitor regularly. Seek medical help for high or persistent fever! 🏥",
                f"To manage body temperature: stay hydrated, rest in a cool environment, use appropriate clothing, and monitor regularly. For fever, you can use over-the-counter fever reducers (as directed), but always consult your doctor for persistent or high fever! 💊"
            ]
            return random.choice(responses)
        
        # 6. Exercise specific
        if any(w in msg_lower for w in ['exercise', 'excise', 'work out', 'workout', 'walk', 'run']):
            responses = [
                f"Moving your body is great for you, {full_name}! 🏃‍♂️ Simple activities like walking, light stretching, or gardening can be very beneficial. Always check with your doctor before starting a new routine!",
                f"Great question! Many people find that a daily 20-minute walk helps improve heart health and mood. 🌿 Just listen to your body and don't overdo it.",
                f"Regular gentle movement is key, {full_name}. You don't need to run a marathon—just staying active helps! Ask your doctor what types of exercise are safe for you. 🧘"
            ]
            return random.choice(responses)

        # 3. Diet specific
        if any(w in msg_lower for w in ['diet', 'food', 'eat', 'nutrition']):
            responses = [
                f"They say 'you are what you eat'! 🍎 Generally, a balanced diet with plenty of vegetables, fruits, and whole grains is recommended. But for your specific needs, a nutritionist or your doctor is the best guide.",
                f"Eating well is a huge part of staying healthy, {full_name}. 🥗 Try to stay hydrated and limit processed foods. Do you have any specific dietary restrictions your doctor mentioned?",
                f"Good nutrition is powerful medicine. 🥕 Focusing on fresh, whole foods is usually a safe bet. However, please consult your doctor for a diet plan that fits your specific health conditions."
            ]
            return random.choice(responses)

        # 3. General Advice / Tips / Control
        advice_keywords = ['how to', 'make it normal', 'improve', 'fix', 'advice', 'change', 'control', 'controll', 'tips', 'tip', 'suggestion', 'suggestions']
        advice_phrases = ['what should i do', 'what do i do', 'what i do', 'what can i do', 'what i so', 'so what i do']
        
        if any(k in msg_lower for k in advice_keywords) or any(p in msg_lower for p in advice_phrases):
            responses = [
                f"That's a good question, {full_name}. Generally, maintaining a healthy diet, staying hydrated, and regular gentle exercise can help. However, since every person is different, the best way to improve your specific condition is to share these readings with your doctor. 🩺",
                f"I love that you're taking charge of your health, {full_name}! 🌟 Small steps like better sleep, drinking water, and reducing stress make a big difference. Be sure to discuss these results with your doctor for a tailored plan.",
                f"Improving your health is a journey! 💙 Focusing on the basics—sleep, hydration, and movement—is a great start. But for these specific readings, your doctor's advice is the most important tool you have."
            ]
            return random.choice(responses)

        # 4. Interpretation (Is it good/bad?)
        if any(w in msg_lower for w in ['good', 'bad', 'normal', 'okay', 'fine', 'worry', 'dangerous', 'safe', 'indicate', 'mean']):
            if "No recent vitals" in context:
                return f"I can't tell yet, {full_name}. Please add some health readings first so I can analyze them for you. 📊"
            
            if "⚠️ Abnormal" in context:
                return f"I see some values that are flagged as abnormal, {full_name}. It's best not to worry, but you should share these results with your doctor just to be safe. 💙"
            elif "✅ Normal" in context:
                return f"Yes, {full_name}! Based on your recent data, everything looks within the normal range. Keep up the good work! 🎉"
            else:
                return f"I'm not sure, {full_name}. I don't see enough data to give you a clear answer. Please try adding more readings."

        # Check if asking about vitals (General)
        if any(word in msg_lower for word in ['vitals', 'health', 'data', 'readings', 'condition', 'status']):
            if "No recent vitals" in context:
                return f"I don't see any health data recorded yet, {full_name}. Would you like to add some vitals in the Settings page? 📊"
            else:
                if "⚠️ Abnormal" in context:
                    return f"Here's your recent health data, {full_name}:\n\n{context}\n\nI noticed some values are outside the typical range. Please consult with your doctor to understand what this means for you. 💙"
                else:
                    return f"Here's what I found in your recent health data, {full_name}:\n\n{context}\n\nEverything looks good! Keep monitoring regularly. 💙"
        
        # Check if asking about specific vital (Value extraction or Definition)
        import re
        
        def get_latest_value(vital_type, text):
            # Regex to find lines like: - YYYY-MM-DD HH:MM: type = value unit
            match = re.search(f"{vital_type} = ([\d\.]+) (\w+)", text)
            if match:
                return f"{match.group(1)} {match.group(2)}"
            return None

        check_keywords = ['my', 'is', 'value', 'check', 'about', 'tell']

        if 'heart' in msg_lower or 'hr' in msg_lower or 'pulse' in msg_lower:
            if any(k in msg_lower for k in check_keywords):
                val = get_latest_value('heart_rate', context)
                if val:
                    return f"Your latest heart rate reading was {val}. Normal resting heart rate is typically 60-100 bpm. ❤️"
                else:
                    return f"I don't see a recent heart rate reading in your data, {full_name}. Please add one in the Settings page! 💓"
            return "Your heart rate is an important indicator of cardiovascular health. Normal resting heart rate is typically 60-100 bpm. If you notice anything unusual, please consult your doctor. ❤️"
        
        if 'blood pressure' in msg_lower or 'bp' in msg_lower:
            if any(k in msg_lower for k in check_keywords):
                sys = get_latest_value('blood_pressure_sys', context)
                dia = get_latest_value('blood_pressure_dia', context)
                if sys and dia:
                    return f"Your latest blood pressure was {sys} (systolic) / {dia} (diastolic). Normal is typically below 120/80. 🩺"
                else:
                    return f"I don't see a full blood pressure reading recently, {full_name}. Please update your vitals! 🩺"
            return "Blood pressure is measured as systolic/diastolic (e.g., 120/80). Normal is typically below 120/80. High blood pressure should be monitored by a healthcare professional. 🩺"
        
        if 'oxygen' in msg_lower or 'spo2' in msg_lower:
            if any(k in msg_lower for k in check_keywords):
                val = get_latest_value('spo2', context)
                if val:
                    return f"Your latest SpO2 reading was {val}. Levels below 95% may need medical attention. 🫁"
                else:
                    return f"I don't see a recent SpO2 reading, {full_name}. 🫁"
            return "Blood oxygen (SpO2) should typically be 95-100%. Levels below 95% may need medical attention. Make sure to measure it properly! 🫁"
        
        if 'glucose' in msg_lower or 'sugar' in msg_lower or 'diabetes' in msg_lower:
            if any(k in msg_lower for k in check_keywords):
                val = get_latest_value('glucose', context)
                if val:
                    return f"Your latest glucose reading was {val}. Normal fasting glucose is 70-100 mg/dL. 🩸"
                else:
                    return f"I don't see a recent glucose reading, {full_name}. 🩸"
            return "Normal fasting glucose is 70-100 mg/dL. After meals, it can go up to 140 mg/dL. If you have diabetes, follow your doctor's guidance on target ranges. 🩸"
        
        if 'temperature' in msg_lower or 'fever' in msg_lower:
            if any(k in msg_lower for k in check_keywords):
                val = get_latest_value('temperature', context)
                if val:
                    return f"Your latest temperature was {val}. Normal body temperature is around 98.6°F. 🌡️"
                else:
                    return f"I don't see a recent temperature reading, {full_name}. 🌡️"
            return "Normal body temperature is around 98.6°F (37°C). A fever is generally 100.4°F or higher. If you have a persistent fever, contact your doctor. 🌡️"
        
        # Greetings
        if any(word in msg_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return f"Hello{greeting_name}! 👋 I'm your AI Health Companion. I can help you understand your health data and answer questions about your vitals. How can I assist you today?"
        
        # General health question
        if '?' in user_message:
            return f"That's a great question, {full_name}! While I can help you understand your health data, I recommend discussing specific medical concerns with your doctor. Is there anything about your recent vitals you'd like me to explain? 💙"
        
        # Default friendly response
        return f"I'm here to help you understand your health data, {full_name}! You can ask me about your vitals, or add new readings in the Settings page. What would you like to know? 😊"

# Singleton instance
agent = HealthAgent()
