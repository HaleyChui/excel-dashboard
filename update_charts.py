replacements = [
    ('"backgroundColor:\'#1A1A1A\',borderColor:\'#2A2A2A\',textStyle:{color:\'#FFF\',fontSize:12}"', 
     '"backgroundColor:\'#ffffff\',borderColor:\'#e2e8f0\',textStyle:{color:\'#0f172a\',fontSize:12}"'),
    ("backgroundColor:'#1A1A1A',borderColor:'#2A2A2A',textStyle:{color:'#FFF',fontSize:12}",
     "backgroundColor:'#ffffff',borderColor:'#e2e8f0',textStyle:{color:'#0f172a',fontSize:12}"),
    
    ('"axisLine:{lineStyle:{color:\'#2A2A2A\'}}"', 
     '"axisLine:{lineStyle:{color:\'#e2e8f0\'}}"'),
    
    ('"splitLine:{lineStyle:{color:\'#1A1A1A\'}}"',
     '"splitLine:{lineStyle:{color:\'#e2e8f0\',type:\'dashed\'}}"'),
    ('"splitLine:{lineStyle:{color:\'#1A1A1A\',type:\'dashed\'}}"',
     '"splitLine:{lineStyle:{color:\'#e2e8f0\',type:\'dashed\'}}"'),
    
    ('"axisLabel:{color:\'#828282\'}"',
     '"axisLabel:{color:\'#475569\',fontSize:11}"'),
    ('"axisLabel:{color:\'#828282\',fontSize:10,rotate:30}"',
     '"axisLabel:{color:\'#475569\',fontSize:10,rotate:30}"'),
    ('"axisLabel:{color:\'#828282\',fontSize:11}"',
     '"axisLabel:{color:\'#475569\',fontSize:11}"'),
    
    ('"label:{color:\'#AAA\',fontSize:11,formatter:\'\\{b\\\\n\\{d\\}%\'}"',
     '"label:{color:\'#475569\',fontSize:11,formatter:\'\\{b\\\\n\\{d\\}%\'}"'),
    ('"label:{color:\'#FFF\',fontSize:12,formatter:\'\\{b\\\\n\\{c\'}',
     '"label:{color:\'#0f172a\',fontSize:12,formatter:\'\\{b\\\\n\\{c\'}'),
    
    ('"labelLine:{lineStyle:{color:\'#2A2A2A\'}}"',
     '"labelLine:{lineStyle:{color:\'#e2e8f0\'}}"'),
    
    ('"itemStyle:{borderColor:\'#141414\',borderWidth:2}"',
     '"itemStyle:{borderColor:\'#ffffff\',borderWidth:1}"'),
    ('"itemStyle:{borderColor:\'#141414\',borderWidth:2,shadowBlur:10,shadowColor:\'rgba(0,0,0,0.5)\'}"',
     '"itemStyle:{borderColor:\'#ffffff\',borderWidth:1,shadowBlur:8,shadowColor:\'rgba(0,0,0,0.1)\'}"'),
    
    ('"splitLine:{lineStyle:{color:\'#2A2A2A\'}}"',
     '"splitLine:{lineStyle:{color:\'#e2e8f0\'}}"'),
    
    ('"splitArea:{areaStyle:{color:[\'rgba(255,255,255,0.02)\',\'rgba(255,255,255,0.05)\']}}"',
     '"splitArea:{areaStyle:{color:[\'rgba(0,0,0,0.02)\',\'rgba(0,0,0,0.05)\']}}"'),
    
    ('"axisName:{color:\'#828282\',fontSize:11}"',
     '"axisName:{color:\'#94a3b8\',fontSize:11}"'),
    
    ('"xAxis:{type:\'value\',splitLine:{lineStyle:{color:\'#1A1A1A\'}},axisLabel:{color:\'#828282\'}}"',
     '"xAxis:{type:\'value\',splitLine:{lineStyle:{color:\'#e2e8f0\',type:\'dashed\'}},axisLabel:{color:\'#94a3b8\'}}"'),
    ('"yAxis:{type:\'value\',splitLine:{lineStyle:{color:\'#1A1A1A\'}},axisLabel:{color:\'#828282\'}}"',
     '"yAxis:{type:\'value\',splitLine:{lineStyle:{color:\'#e2e8f0\',type:\'dashed\'}},axisLabel:{color:\'#94a3b8\'}}"'),
    
    ('"areaStyle:{color:\'" + color + "\'15}"',
     '"areaStyle:{color:\'" + color + "\'20}"'),
]

print("Total replacements:", len(replacements))

# Read file
with open('/home/cryptochyi629/Dashboard_Gen/excel-dashboard/backend/llm_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Apply replacements
for old, new in replacements:
    before = content.count(old)
    if before > 0:
        content = content.replace(old, new)
        print(f"Replaced {before} occurrences of: {old[:60]}...")

# Write back
with open('/home/cryptochyi629/Dashboard_Gen/excel-dashboard/backend/llm_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")