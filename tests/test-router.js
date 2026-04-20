import OpenAI from "openai";
import 'dotenv/config';

const openai = new OpenAI({
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY,
});

async function test() {
    try {
        const completion = await openai.chat.completions.create({
            model: "google/gemini-2.0-flash-001", // This is a great, fast default
            messages: [{ role: "user", content: "Confirming connectivity!" }],
        });
        console.log("Response:", completion.choices[0].message.content);
        console.log("✅ OpenRouter is ready to go!");
    } catch (error) {
        console.error("❌ Connection failed:", error.message);
    }
}

test();