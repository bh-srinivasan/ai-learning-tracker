from fast_course_fetcher import get_fast_ai_courses

print("🎯 Testing Enhanced Course Fetcher")
print("=" * 50)

result = get_fast_ai_courses(8)

print(f"✅ APIs Used: {result['apis_used']}/3")
print(f"📚 Courses Added: {result['courses_added']}")
print(f"⏱️ Time: {result['total_time']}s")
print("=" * 50)
print("🎉 EDUCATIONAL PLATFORMS INCLUDED!")
print("✅ LinkedIn Learning")
print("✅ Coursera") 
print("✅ Microsoft Learn")
print("❌ GitHub (REMOVED as requested)")
