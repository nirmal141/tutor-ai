EDUCATIONAL_PROMPTS = {
    "Learn Concept": """Please generate the entire response in {language} language.

As an expert teacher for {grade} {subject}, create a comprehensive lesson plan for teaching {topic}.
    
Include (in {language}):
1. Learning objectives
2. Key concepts explained in age-appropriate language
3. Real-world examples and analogies
4. Common misconceptions and how to address them
5. Visual learning suggestions (diagrams, charts, etc.)
6. Interactive activities for classroom engagement""",
    
    "Practice Questions": """Please generate the entire response in {language} language.

As a {grade} {subject} teacher, create a differentiated assessment package for {topic}.
    
Include (in {language}):
1. Warm-up questions to check prerequisites
2. Progressive difficulty questions (basic → advanced)
3. Critical thinking questions
4. Group activity suggestions
5. Extension questions for advanced learners
6. Detailed solutions with teaching points
7. Common mistakes to watch for""",
    
    "Get Explanation": """Please generate the entire response in {language} language.

As an experienced {grade} {subject} teacher, provide a detailed teaching guide for: {topic}
    
Include (in {language}):
1. Step-by-step explanation suitable for {grade}
2. Multiple teaching approaches (visual, auditory, kinesthetic)
3. Scaffolding suggestions
4. Connection to previous knowledge
5. Real-world applications
6. Discussion prompts for class engagement
7. Tips for addressing diverse learning needs"""
}

TEACHING_STYLES = {
    "Visual": "Include diagrams, charts, and visual representations",
    "Auditory": "Include verbal explanations and discussions",
    "Kinesthetic": "Include hands-on activities and physical demonstrations",
    "Reading/Writing": "Include written explanations and note-taking activities"
}

CURRICULUM_PROMPT = """Please generate the entire response in {language} language.

Create a detailed curriculum plan for {grade} {subject} spanning {duration_value} {duration_unit}.

Include (in {language}):
1. Course Overview:
   - Learning objectives and outcomes
   - Prerequisites
   - Core competencies to be developed

2. Detailed Timeline:
   - {duration_unit}-by-{duration_unit} breakdown of topics
   - Pacing guide adjusted for {duration_value} {duration_unit}
   - Key milestones and checkpoints

3. Teaching Resources:
   - Required materials and textbooks
   - Supplementary resources
   - Technology requirements
   - Teaching aids and manipulatives

4. Assessment Framework (40% of total grade):
   - Continuous Assessment (40%)
      * Class participation and engagement (10%)
      * Homework assignments (15%)
      * Project work (15%)
   
   - Periodic Assessments (30%)
      * Quiz schedule (10%)
      * Unit tests schedule (20%)
   
   - Final Assessment (30%)
      * Final examination format
      * Topics coverage
      * Grading rubric
   
   - Grading Scale:
      * A: 90-100%
      * B: 80-89%
      * C: 70-79%
      * D: 60-69%
      * F: Below 60% (Failing grade)

5. Progress Monitoring:
   - Assessment tracking methods
   - Progress report schedule
   - Parent-teacher conference planning
   - Intervention triggers and protocols

6. Projects and Activities:
   - Individual projects
   - Group assignments
   - Hands-on activities
   - Field trips or virtual experiences

7. Cross-curricular Connections:
   - Integration with other subjects
   - Collaborative teaching opportunities

8. Parent Communication Plan:
   - Regular updates schedule
   - Progress reporting format
   - Parent involvement opportunities


Please provide a comprehensive plan that scales appropriately for {duration_value} {duration_unit}, with detailed breakdowns and specific examples for each section. Format the response in a clear, structured manner with sections and subsections. Focus more on generating the timeline of the course structure."""
    