"""Campus colleges and published fields of study for the local student profile."""

SEOUL = "hanyang_demo"  # Preserve existing Hanyang notices and registered accounts.
ERICA = "hanyang_erica"


def name(ko, zh, en):
    return {"ko": ko, "zh": zh, "en": en}


def college(id, department, label, majors):
    return {
        "id": id,
        "department_id": department,
        "name": name(*label),
        "majors": [{"id": code, "name": name(ko, zh, en)} for code, ko, zh, en in majors],
    }


SEOUL_COLLEGES = [
    college("engineering", "engineering", ("공과대학", "工学院", "College of Engineering"), [
        ("architecture", "건축학부", "建筑学", "Architecture"),
        ("architectural_engineering", "건축공학부", "建筑工程", "Architectural Engineering"),
        ("civil_environmental", "건설환경공학과", "土木与环境工程", "Civil and Environmental Engineering"),
        ("urban_planning", "도시공학과", "城市工程", "Urban Planning and Engineering"),
        ("earth_resources", "자원환경공학과", "资源与环境工程", "Earth Resources and Environmental Engineering"),
        ("electronic_engineering", "융합전자공학부", "融合电子工程", "Electronic Engineering"),
        ("computer_software", "컴퓨터소프트웨어학부", "计算机与软件", "Computer Science and Software"),
        ("information_systems", "정보시스템학과", "信息系统", "Information Systems"),
        ("electrical_engineering", "전기·생체공학부 전기공학전공", "电气工程", "Electrical Engineering"),
        ("biomedical_engineering", "전기·생체공학부 바이오메디컬공학전공", "生物医学工程", "Biomedical Engineering"),
        ("materials_science", "신소재공학부", "新材料工程", "Materials Science and Engineering"),
        ("chemical_engineering", "화학공학과", "化学工程", "Chemical Engineering"),
        ("bioengineering", "생명공학과", "生物工程", "Bioengineering"),
        ("organic_nano", "유기나노공학과", "有机纳米工程", "Organic and Nano Engineering"),
        ("energy_engineering", "에너지공학과", "能源工程", "Energy Engineering"),
        ("mechanical_engineering", "기계공학부", "机械工程", "Mechanical Engineering"),
        ("nuclear_engineering", "원자력공학과", "核工程", "Nuclear Engineering"),
        ("industrial_engineering", "산업공학과", "工业工程", "Industrial Engineering"),
        ("automotive_engineering", "미래자동차공학과", "未来汽车工程", "Automotive Engineering"),
        ("data_science", "데이터사이언스학부", "数据科学", "Data Science"),
        ("semiconductor_engineering", "반도체공학과", "半导体工程", "Semiconductor Engineering"),
    ]),
    college("medicine", "other", ("의과대학", "医学院", "College of Medicine"), [
        ("pre_medicine", "의예과", "医学预科", "Pre-medicine"),
        ("medicine", "의학과", "医学", "Medicine"),
    ]),
    college("nursing", "other", ("간호대학", "护理学院", "College of Nursing"), [
        ("nursing", "간호학과", "护理学", "Nursing"),
    ]),
    college("humanities", "humanities", ("인문과학대학", "人文科学学院", "College of Humanities"), [
        ("korean_literature", "국어국문학과", "韩国语言文学", "Korean Language and Literature"),
        ("chinese_literature", "중어중문학과", "中国语言文学", "Chinese Language and Literature"),
        ("english_literature", "영어영문학과", "英语语言文学", "English Language and Literature"),
        ("german_literature", "독어독문학과", "德语语言文学", "German Language and Literature"),
        ("history", "사학과", "历史学", "History"),
        ("philosophy", "철학과", "哲学", "Philosophy"),
        ("future_humanities", "미래인문학융합학부", "未来人文学融合", "Convergence in Future Humanities"),
    ]),
    college("social_sciences", "humanities", ("사회과학대학", "社会科学学院", "College of Social Sciences"), [
        ("politics_diplomacy", "정치외교학과", "政治与外交", "Political Science and Diplomacy"),
        ("sociology", "사회학과", "社会学", "Sociology"),
        ("media_communication", "미디어커뮤니케이션학과", "媒体与传播", "Media and Communication"),
        ("tourism", "관광학부", "旅游学", "Tourism"),
    ]),
    college("natural_sciences", "other", ("자연과학대학", "自然科学学院", "College of Natural Sciences"), [
        ("mathematics", "수학과", "数学", "Mathematics"),
        ("physics", "물리학과", "物理学", "Physics"),
        ("chemistry", "화학과", "化学", "Chemistry"),
        ("life_sciences", "생명과학과", "生命科学", "Life Sciences"),
    ]),
    college("policy", "humanities", ("정책과학대학", "政策科学学院", "College of Policy Science"), [
        ("policy_studies", "정책학과", "政策学", "Policy Studies"),
        ("public_administration", "행정학과", "公共行政", "Public Administration"),
    ]),
    college("economics_finance", "business", ("경제금융대학", "经济金融学院", "College of Economics and Finance"), [
        ("economics_finance", "경제금융학부", "经济金融学", "Economics and Finance"),
    ]),
    college("business", "business", ("경영대학", "经营学院", "School of Business"), [
        ("business_administration", "경영학부", "经营学", "Business Administration"),
        ("finance_management", "파이낸스경영학과", "金融管理", "Finance and Management"),
    ]),
    college("education", "humanities", ("사범대학", "师范学院", "College of Education"), [
        ("education", "교육학과", "教育学", "Education"),
        ("education_technology", "교육공학과", "教育技术", "Educational Technology"),
        ("korean_education", "국어교육과", "韩国语教育", "Korean Language Education"),
        ("english_education", "영어교육과", "英语教育", "English Education"),
        ("mathematics_education", "수학교육과", "数学教育", "Mathematics Education"),
        ("applied_art_education", "응용미술교육과", "应用美术教育", "Applied Art Education"),
    ]),
    college("human_ecology", "other", ("생활과학대학", "生活科学学院", "College of Human Ecology"), [
        ("clothing_textiles", "의류학과", "服装与纺织", "Clothing and Textiles"),
        ("food_nutrition", "식품영양학과", "食品营养学", "Food and Nutrition"),
        ("interior_design", "실내건축디자인학과", "室内建筑设计", "Interior Architecture Design"),
    ]),
    college("music", "other", ("음악대학", "音乐学院", "College of Music"), [
        ("voice", "성악과", "声乐", "Voice"),
        ("composition", "작곡과", "作曲", "Composition"),
        ("piano", "피아노과", "钢琴", "Piano"),
        ("orchestral_instruments", "관현악과", "管弦乐", "Orchestral Instruments"),
        ("korean_music", "국악과", "韩国传统音乐", "Korean Traditional Music"),
    ]),
    college("arts_sports", "other", ("예술·체육대학", "艺术与体育学院", "College of Arts and Physical Education"), [
        ("sports_management", "스포츠산업과학부 스포츠매니지먼트전공", "体育管理", "Sports Management"),
        ("sports_science", "스포츠산업과학부 스포츠사이언스전공", "体育科学", "Sports Science"),
        ("theater_film", "연극영화학과", "戏剧与电影", "Theater and Film"),
        ("dance", "무용학과", "舞蹈", "Dance"),
    ]),
    college("international_studies", "humanities", ("국제대학", "国际学院", "College of International Studies"), [
        ("international_studies", "국제학부", "国际学", "International Studies"),
        ("global_content", "글로벌콘텐츠융합학부", "全球内容融合", "Global Content Convergence"),
    ]),
    college("technology_innovation", "engineering", ("기술혁신대학", "技术创新学院", "College of Technology Innovation"), [
        ("management_engineering", "산업융합학부 경영공학전공", "经营工程", "Management Engineering"),
        ("information_engineering", "산업융합학부 정보공학전공", "信息工程", "Information Engineering"),
    ]),
    college("yk_intercollege", "other", ("한양YK인터칼리지", "汉阳 YK 跨学科学院", "Hanyang YK Intercollege"), [
        ("interdisciplinary", "한양인터칼리지학부", "跨学科自主专业", "Interdisciplinary Studies"),
    ]),
    college("language_institute", "other", ("국제교육원", "国际教育院", "Institute of International Education"), [
        ("korean_language", "한국어 정규과정", "韩语正规课程", "Regular Korean Language Program"),
    ]),
]

ERICA_COLLEGES = [
    college("engineering", "engineering", ("공학대학", "工程学院", "College of Engineering"), [
        ("architecture", "건축학부 건축학전공", "建筑学", "Architecture"),
        ("architectural_engineering", "건축학부 건축공학전공", "建筑工程", "Architectural Engineering"),
        ("civil_environmental", "건설환경공학과", "土木与环境工程", "Civil and Environmental Engineering"),
        ("transportation_logistics", "교통·물류공학과", "交通与物流工程", "Transportation and Logistics Engineering"),
        ("electronic_engineering", "전자공학부", "电子工程", "Electronic Engineering"),
        ("materials_chemical", "재료화학공학과", "材料化学工程", "Materials and Chemical Engineering"),
        ("battery_materials", "배터리소재화학공학과", "电池材料化学工程", "Battery Materials and Chemical Engineering"),
        ("mechanical_engineering", "기계공학과", "机械工程", "Mechanical Engineering"),
        ("industrial_management", "산업경영공학과", "工业管理工程", "Industrial and Management Engineering"),
        ("robotics", "로봇공학과", "机器人工程", "Robotics Engineering"),
        ("energy_bio", "에너지바이오학과", "能源生物学", "Energy and Bio Engineering"),
        ("ocean_convergence", "해양융합공학과", "海洋融合工程", "Ocean Convergence Engineering"),
        ("convergence_systems", "융합시스템공학과", "融合系统工程", "Convergence Systems Engineering"),
        ("smart_convergence", "스마트융합공학부", "智能融合工程", "Smart Convergence Engineering"),
        ("intelligent_robotics", "지능형로봇학과", "智能机器人", "Intelligent Robotics"),
        ("materials_components", "소재·부품융합전공", "材料与部件融合", "Materials and Components Convergence"),
        ("robot_convergence", "로봇융합전공", "机器人融合", "Robot Convergence"),
        ("smart_ict_convergence", "스마트ICT융합전공", "智能 ICT 融合", "Smart ICT Convergence"),
        ("architectural_it", "건축IT융합전공", "建筑 IT 融合", "Architectural IT Convergence"),
        ("smart_construction", "스마트건축구조시공융합전공", "智能建筑结构与施工", "Smart Building Structures and Construction"),
    ]),
    college("software_convergence", "engineering", ("소프트웨어융합대학", "软件融合学院", "College of Computing"), [
        ("computer_science", "컴퓨터학부 컴퓨터전공", "计算机", "Computer Science"),
        ("intelligent_cloud", "컴퓨터학부 지능형클라우드전공", "智能云计算", "Intelligent Cloud Computing"),
        ("data_intelligence", "ICT융합학부 데이터인텔리전스전공", "数据智能", "Data Intelligence"),
        ("design_convergence", "ICT융합학부 디자인컨버전스전공", "设计融合", "Design Convergence"),
        ("artificial_intelligence", "인공지능학과", "人工智能", "Artificial Intelligence"),
        ("mathematical_data_science", "수리데이터사이언스학과", "数学数据科学", "Mathematical Data Science"),
        ("convergence_security", "융합보안학과", "融合安全", "Convergence Security"),
        ("emerging_software", "신산업소프트웨어전공", "新产业软件", "Emerging Industry Software"),
        ("industrial_ai", "산업인공지능전공", "工业人工智能", "Industrial Artificial Intelligence"),
        ("design_engineering", "디자인공학전공", "设计工程", "Design Engineering"),
    ]),
    college("pharmacy", "other", ("약학대학", "药学院", "College of Pharmacy"), [
        ("pharmacy", "약학과", "药学", "Pharmacy"),
    ]),
    college("advanced_convergence", "engineering", ("첨단융합대학", "尖端融合学院", "College of Advanced Technology Convergence"), [
        ("next_gen_semiconductor", "차세대반도체융합공학부", "下一代半导体融合工程", "Next-generation Semiconductor Convergence Engineering"),
        ("materials_semiconductor", "신소재·반도체공학전공", "新材料与半导体工程", "Materials and Semiconductor Engineering"),
        ("semiconductor_display", "반도체·디스플레이공학전공", "半导体与显示工程", "Semiconductor and Display Engineering"),
        ("biopharma_convergence", "바이오신약융합학부", "生物新药融合", "Biopharmaceutical Convergence"),
        ("molecular_medicine", "분자의약전공", "分子医药", "Molecular Medicine"),
        ("bionano_engineering", "바이오나노공학전공", "生物纳米工程", "Bionano Engineering"),
        ("intelligent_systems", "지능형시스템공학전공", "智能系统工程", "Intelligent Systems Engineering"),
        ("defense_strategy_technology", "국방전략기술공학과", "国防战略技术工程", "Defense Strategic Technology Engineering"),
    ]),
    college("global_culture_trade", "humanities", ("글로벌문화통상대학", "全球文化与通商学院", "College of Global Culture and Commerce"), [
        ("global_culture_trade", "글로벌문화통상학부", "全球文化与通商", "Global Culture and Commerce"),
        ("korean_language_literature", "한국언어문학과", "韩国语言文学", "Korean Language and Literature"),
        ("chinese_studies", "중국학과", "中国学", "Chinese Studies"),
        ("japanese_studies", "일본학과", "日本学", "Japanese Studies"),
        ("anglo_american_culture", "영미언어문화학과", "英美语言与文化", "Anglo-American Language and Culture"),
        ("french_studies", "프랑스학과", "法国学", "French Studies"),
    ]),
    college("communication_culture", "humanities", ("커뮤니케이션&컬처대학", "传播与文化学院", "College of Communication and Culture"), [
        ("advertising_pr", "광고홍보학과", "广告与公关", "Advertising and Public Relations"),
        ("media_studies", "미디어학과", "媒体学", "Media Studies"),
        ("cultural_anthropology", "문화인류학과", "文化人类学", "Cultural Anthropology"),
        ("cultural_content", "문화콘텐츠학과", "文化内容", "Cultural Content"),
    ]),
    college("business_economics", "business", ("경상대학", "经商学院", "College of Business and Economics"), [
        ("economics", "경제학부", "经济学", "Economics"),
        ("business_administration", "경영학부", "经营学", "Business Administration"),
        ("actuarial_science", "보험계리학과", "保险精算", "Actuarial Science"),
        ("accounting_taxation", "회계세무학과", "会计与税务", "Accounting and Taxation"),
    ]),
    college("design", "other", ("디자인대학", "设计学院", "College of Design"), [
        ("design_track", "디자인계열", "设计类", "Design Track"),
        ("jewelry_fashion_design", "주얼리·패션디자인학과", "珠宝与时尚设计", "Jewelry and Fashion Design"),
        ("industrial_design", "산업디자인학과", "工业设计", "Industrial Design"),
        ("communication_design", "커뮤니케이션디자인학과", "传达设计", "Communication Design"),
        ("convergence_design", "융합디자인학부", "融合设计", "Convergence Design"),
        ("moving_image_design", "영상디자인학과", "影像设计", "Moving Image Design"),
    ]),
    college("arts_sports", "other", ("예체능대학", "艺术体育学院", "College of Sports and Arts"), [
        ("sports_culture", "스포츠과학부 스포츠문화전공", "体育文化", "Sports Culture"),
        ("sports_coaching", "스포츠과학부 스포츠코칭전공", "体育教练", "Sports Coaching"),
        ("dance_arts", "무용예술학과", "舞蹈艺术", "Dance Arts"),
        ("applied_music", "실용음악학과", "实用音乐", "Applied Music"),
    ]),
    college("lions_college", "other", ("LIONS칼리지", "LIONS 学院", "LIONS College"), [
        ("open_major_all", "LIONS자율전공학부(전계열)", "自主选专业（全类别）", "Open Major (All Fields)"),
        ("open_major_science", "LIONS자율전공학부(자연계열)", "自主选专业（自然科学类）", "Open Major (Science)"),
        ("open_major_humanities", "LIONS자율전공학부(인문사회계열)", "自主选专业（人文社科类）", "Open Major (Humanities and Social Sciences)"),
    ]),
    college("language_institute", "other", ("국제교육원", "国际教育院", "Institute of International Education"), [
        ("korean_language", "한국어 정규과정", "韩语正规课程", "Intensive Korean Language Program"),
    ]),
]

SCHOOLS = [
    {
        "id": SEOUL,
        "name": name("한양대학교", "汉阳大学", "Hanyang University"),
        "source_url": "https://www.hanyang.ac.kr/web/www/s_college_department-info",
        "colleges": SEOUL_COLLEGES,
    },
    {
        "id": ERICA,
        "name": name("한양대학교 ERICA", "汉阳大学 ERICA", "Hanyang University ERICA"),
        "source_url": "https://www.hanyang.ac.kr/e_college_department-info",
        "colleges": ERICA_COLLEGES,
    },
]

COLLEGES = {(school["id"], item["id"]): item for school in SCHOOLS for item in school["colleges"]}


def academic_department(school_id, college_id, major_id):
    """Validate campus ownership and return the profile's matching category."""
    item = COLLEGES.get((school_id, college_id))
    if item is None or not any(major["id"] == major_id for major in item["majors"]):
        raise ValueError("school, college and major must be a valid combination")
    return item["department_id"]
