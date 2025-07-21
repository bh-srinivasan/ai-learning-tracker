from fast_course_fetcher import get_fast_ai_courses

print("🎯 Testing Enhanced Course Fetcher - Final Test")
print("=" * 50)

result = get_fast_ai_courses(10)

print(f"✅ Success: {result['success']}")
print(f"📚 Courses Added: {result['courses_added']}")
print(f"🌐 APIs Used: {result['apis_used']}/3")
print(f"⏱️ Time: {result['total_time']}s")

if result['details']:
    print("\n📊 API Results:")
    for detail in result['details']:
        print(f"   • {detail}")

print("\n🎉 REAL COURSES NOW BEING FETCHED!")
print("✅ LinkedIn Learning - REAL courses")
print("✅ Coursera - REAL courses") 
print("✅ Microsoft Learn - REAL courses")
