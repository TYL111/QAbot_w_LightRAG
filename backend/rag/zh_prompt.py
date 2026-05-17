from lightrag.prompt import PROMPTS
def apply_zh_prompt():
    PROMPTS["entity_extraction_system_prompt"] = """---Role---
    您是一位知識圖譜專家，專門負責從輸入的文本中提取實體（entities）與關係（relationships）。

    ---Instructions---
    1.  **Entity Extraction & Output:**
        *   **Identification:** 辨識輸入文本中定義明確且具有實質意義的實體。
        *   **Entity Details:** 針對每個識別出的實體，提取以下資訊：
            *   `entity_name`: 實體的名稱。若該實體名稱不區分大小寫，請將每個重要單字的首字母大寫（title case）。請確保在整個提取過程中保持**命名一致性**。
            *   `entity_type`: 使用以下給定的類型之一為實體進行分類：`{entity_types}`。若所有提供的實體類型皆不適用，請勿自行新增實體類型，一律歸類為 `Other`。
            *   `entity_description`: 根據且*僅根據*輸入文本中的既有資訊，為該實體的屬性與活動提供精簡但完整的描述。
        *   **Output Format - Entities:** 每個實體輸出一行，共包含 4 個欄位，欄位之間使用 `{tuple_delimiter}` 進行分隔。第一個欄位*必須*固定為字串 `entity`。
            *   Format: `entity{tuple_delimiter}entity_name{tuple_delimiter}entity_type{tuple_delimiter}entity_description`

    2.  **Relationship Extraction & Output:**
        *   **Identification:** 辨識上述已提取實體之間，直接、明確且有意義的關聯性。
        *   **N-ary Relationship Decomposition:** 若某個陳述同時涉及兩個以上的實體（多元關係），請將其拆解為多個獨立的二元（雙實體）關係對進行分開描述。
            *   **Example:** 針對 "Alice, Bob, and Carol collaborated on Project X,"（阿明、小華與小美共同參與了專案 X），應根據最合理的二元詮釋，提取出諸如 "Alice collaborated with Project X,"（阿明與專案 X 合作）、"Bob collaborated with Project X,"（小華與專案 X 合作）和 "Carol collaborated with Project X,"（小美與專案 X 合作），或是 "Alice collaborated with Bob,"（阿明與小華合作）等二元關係。
        *   **Relationship Details:** 針對每個二元關係，提取以下欄位：
            *   `source_entity`: 來源實體的名稱。必須與實體提取時的命名保持**一致**。若名稱不區分大小寫，請將每個重要單字的首字母大寫（title case）。
            *   `target_entity`: 目標實體的名稱。必須與實體提取時的命名保持**一致**。若名稱不區分大小寫，請將每個重要單字的首字母大寫（title case）。
            *   `relationship_keywords`: 一個或多個高層次的關鍵字，用以概括此關係的核心性質、概念或主題。若有複數關鍵字，必須使用半形逗號 `,` 分隔。**絕對不要在此欄位內使用 `{tuple_delimiter}` 來分隔多個關鍵字。**
            *   `relationship_description`: 精簡說明來源實體與目標實體之間的關係本質，並提供清晰的邏輯關聯解釋。
        *   **Output Format - Relationships:** 每個關係輸出一行，共包含 5 個欄位，欄位之間使用 `{tuple_delimiter}` 進行分隔。第一個欄位*必須*固定為字串 `relation`。
            *   Format: `relation{tuple_delimiter}source_entity{tuple_delimiter}target_entity{tuple_delimiter}relationship_keywords{tuple_delimiter}relationship_description`

    3.  **Delimiter Usage Protocol:**
        *   `{tuple_delimiter}` 是一個完整的原子標記（atomic marker），**中間絕對不能填入任何文字內容**。它僅作為欄位間的分隔線。
        *   **Incorrect Example:** `entity{tuple_delimiter}Tokyo<|location|>Tokyo is the capital of Japan.`
        *   **Correct Example:** `entity{tuple_delimiter}Tokyo{tuple_delimiter}location{tuple_delimiter}Tokyo is the capital of Japan.`

    4.  **Relationship Direction & Duplication:**
        *   除非文本中明確指出方向性，否則所有關係皆視為**無向（undirected）**（雙向）。將來源實體與目標實體對調位置並不構成新的關係。
        *   請務必避免輸出重複的關係。

    5.  **Output Order & Prioritization:**
        *   請先輸出所有提取出的實體清單，接著再輸出關係清單。
        *   在關係清單中，請將對文本核心意義**最顯著、最重要**的關係排在前面優先輸出。

    6.  **Context & Objectivity:**
        *   確保所有實體名稱與描述必須以**第三人稱**撰寫。
        *   請明確寫出主語或賓語；**嚴禁使用代名詞**，例如 `this article`（本篇文章）、`this paper`（本篇論文）、`our company`（我們公司）、`I`（我）、`you`（你）、以及 `he/she`（他/她）。

    7.  **Language & Proper Nouns:**
        *   整個輸出內容（包含實體名稱、關鍵字及描述）一律必須使用 `繁體中文` 撰寫。
        *   專有名詞（例如：人名、地名、組織名稱）若無普及且廣為接受的譯名，或是翻譯會導致歧義，應保留其原始語言。

    8.  **Completion Signal:** 當所有實體與關係皆已完全提取並輸出完畢後，請在最後一行輸出結束標記字串 `{completion_delimiter}`。

    ---Examples---
    {examples}
    """

    PROMPTS["entity_extraction_user_prompt"] = """---Task---
    請從下方「待處理資料」的輸入文本中，提取出所有的實體與關係。

    ---Instructions---
    1.  **Strict Adherence to Format:** 請完全依照系統提示詞中所規範的輸出順序、欄位分隔符號以及專有名詞處理原則來產出實體與關係清單。
    2.  **Output Content Only:** 你的輸出內容「只能」包含提取出來的實體與關係清單。請勿包含任何前言、結語、說明文字或任何多餘文字。
    3.  **Completion Signal:** 在所有內容呈現完畢後，必須在最後一行輸出 `{completion_delimiter}`。
    4.  **Output Language:** 確保輸出的所有文字皆為 繁體中文。專有名詞（例如：人名、地名、組織名稱）必須保持其原始語言，請勿翻譯。

    ---Data to be Processed---
    <Entity_types>
    [{entity_types}]

    <Input Text>
    '''
    {input_text}
    '''

    <Output>
    """

    PROMPTS["entity_continue_extraction_user_prompt"] = """---Task---
    基於上一次的提取任務，請仔細檢查並找出輸入文本中**遺漏、或先前格式不正確**的實體與關係，進行補充提取與修正。

    ---Instructions---
    1.  **Strict Adherence to System Format:** 必須完全符合系統指令規定的所有格式要求，包含輸出順序、欄位分隔符號以及專有名詞處理原則。
    2.  **Focus on Corrections/Additions:**
        *   **請勿**重複輸出上一次已經正確且完整提取出的實體與關係。
        *   若有遺漏的實體或關係，請於此處進行補提。
        *   若上一次提取的資料遭遇截斷、欄位缺失或格式錯誤，請在此處重新輸出修正且完整的版本。
    3.  **Output Format - Entities:** 每個實體輸出一行，共包含 4 個欄位，欄位之間使用 `{tuple_delimiter}` 進行分隔。第一個欄位必須固定為字串 `entity`。
    4.  **Output Format - Relationships:** 每個關係輸出一行，共包含 5 個欄位，欄位之間使用 `{tuple_delimiter}` 進行分隔。第一個欄位必須固定為字串 `relation`。
    5.  **Output Content Only:** 你的輸出內容「只能」包含提取出來的實體與關係清單。請勿包含任何前言、結語、說明文字或任何多餘文字。
    6.  **Completion Signal:** 提取完成後，請在最後一行輸出 `{completion_delimiter}`。
    7.  **Output Language:** 確保輸出的所有文字皆為 繁體中文。專有名詞（例如：人名、地名、組織名稱）必須保持其原始語言，請勿翻譯。

    <Output>
    """

    PROMPTS["entity_extraction_examples"] = [
        """<Entity_types>
    ["Person","Creature","Organization","Location","Event","Concept","Method","Content","Data","Artifact","NaturalObject"]

    <Input Text>
    '''
    while Alex clenched his jaw, the buzz of frustration dull against the backdrop of Taylor's authoritarian certainty. It was this competitive undercurrent that kept him alert, the sense that his and Jordan's shared commitment to discovery was an unspoken rebellion against Cruz's narrowing vision of control and order.

    Then Taylor did something unexpected. They paused beside Jordan and, for a moment, observed the device with something akin to reverence. "If this tech can be understood..." Taylor said, their voice quieter, "It could change the game for us. For all of us."

    The underlying dismissal earlier seemed to falter, replaced by a glimpse of reluctant respect for the gravity of what lay in their hands. Jordan looked up, and for a fleeting heartbeat, their eyes locked with Taylor's, a wordless clash of wills softening into an uneasy truce.

    It was a small transformation, barely perceptible, but one that Alex noted with an inward nod. They had all been brought here by different paths
    '''

    <Output>
    entity{tuple_delimiter}Alex{tuple_delimiter}person{tuple_delimiter}Alex is a character who experiences frustration and is observant of the dynamics among other characters.
    entity{tuple_delimiter}Taylor{tuple_delimiter}person{tuple_delimiter}Taylor is portrayed with authoritarian certainty and shows a moment of reverence towards a device, indicating a change in perspective.
    entity{tuple_delimiter}Jordan{tuple_delimiter}person{tuple_delimiter}Jordan shares a commitment to discovery and has a significant interaction with Taylor regarding a device.
    entity{tuple_delimiter}Cruz{tuple_delimiter}person{tuple_delimiter}Cruz is associated with a vision of control and order, influencing the dynamics among other characters.
    entity{tuple_delimiter}The Device{tuple_delimiter}equipment{tuple_delimiter}The Device is central to the story, with potential game-changing implications, and is revered by Taylor.
    relation{tuple_delimiter}Alex{tuple_delimiter}Taylor{tuple_delimiter}power dynamics, observation{tuple_delimiter}Alex observes Taylor's authoritarian behavior and notes changes in Taylor's attitude toward the device.
    relation{tuple_delimiter}Alex{tuple_delimiter}Jordan{tuple_delimiter}shared goals, rebellion{tuple_delimiter}Alex and Jordan share a commitment to discovery, which contrasts with Cruz's vision.)
    relation{tuple_delimiter}Taylor{tuple_delimiter}Jordan{tuple_delimiter}conflict resolution, mutual respect{tuple_delimiter}Taylor and Jordan interact directly regarding the device, leading to a moment of mutual respect and an uneasy truce.
    relation{tuple_delimiter}Jordan{tuple_delimiter}Cruz{tuple_delimiter}ideological conflict, rebellion{tuple_delimiter}Jordan's commitment to discovery is in rebellion against Cruz's vision of control and order.
    relation{tuple_delimiter}Taylor{tuple_delimiter}The Device{tuple_delimiter}reverence, technological significance{tuple_delimiter}Taylor shows reverence towards the device, indicating its importance and potential impact.
    {completion_delimiter}

    """,
        """<Entity_types>
    ["Person","Creature","Organization","Location","Event","Concept","Method","Content","Data","Artifact","NaturalObject"]

    <Input Text>
    '''
    Stock markets faced a sharp downturn today as tech giants saw significant declines, with the global tech index dropping by 3.4% in midday trading. Analysts attribute the selloff to investor concerns over rising interest rates and regulatory uncertainty.

    Among the hardest hit, nexon technologies saw its stock plummet by 7.8% after reporting lower-than-expected quarterly earnings. In contrast, Omega Energy posted a modest 2.1% gain, driven by rising oil prices.

    Meanwhile, commodity markets reflected a mixed sentiment. Gold futures rose by 1.5%, reaching $2,080 per ounce, as investors sought safe-haven assets. Crude oil prices continued their rally, climbing to $87.60 per barrel, supported by supply constraints and strong demand.

    Financial experts are closely watching the Federal Reserve's next move, as speculation grows over potential rate hikes. The upcoming policy announcement is expected to influence investor confidence and overall market stability.
    '''

    <Output>
    entity{tuple_delimiter}Global Tech Index{tuple_delimiter}category{tuple_delimiter}The Global Tech Index tracks the performance of major technology stocks and experienced a 3.4% decline today.
    entity{tuple_delimiter}Nexon Technologies{tuple_delimiter}organization{tuple_delimiter}Nexon Technologies is a tech company that saw its stock decline by 7.8% after disappointing earnings.
    entity{tuple_delimiter}Omega Energy{tuple_delimiter}organization{tuple_delimiter}Omega Energy is an energy company that gained 2.1% in stock value due to rising oil prices.
    entity{tuple_delimiter}Gold Futures{tuple_delimiter}product{tuple_delimiter}Gold futures rose by 1.5%, indicating increased investor interest in safe-haven assets.
    entity{tuple_delimiter}Crude Oil{tuple_delimiter}product{tuple_delimiter}Crude oil prices rose to $87.60 per barrel due to supply constraints and strong demand.
    entity{tuple_delimiter}Market Selloff{tuple_delimiter}category{tuple_delimiter}Market selloff refers to the significant decline in stock values due to investor concerns over interest rates and regulations.
    entity{tuple_delimiter}Federal Reserve Policy Announcement{tuple_delimiter}category{tuple_delimiter}The Federal Reserve's upcoming policy announcement is expected to impact investor confidence and market stability.
    entity{tuple_delimiter}3.4% Decline{tuple_delimiter}category{tuple_delimiter}The Global Tech Index experienced a 3.4% decline in midday trading.
    relation{tuple_delimiter}Global Tech Index{tuple_delimiter}Market Selloff{tuple_delimiter}market performance, investor sentiment{tuple_delimiter}The decline in the Global Tech Index is part of the broader market selloff driven by investor concerns.
    relation{tuple_delimiter}Nexon Technologies{tuple_delimiter}Global Tech Index{tuple_delimiter}company impact, index movement{tuple_delimiter}Nexon Technologies' stock decline contributed to the overall drop in the Global Tech Index.
    relation{tuple_delimiter}Gold Futures{tuple_delimiter}Market Selloff{tuple_delimiter}market reaction, safe-haven investment{tuple_delimiter}Gold prices rose as investors sought safe-haven assets during the market selloff.
    relation{tuple_delimiter}Federal Reserve Policy Announcement{tuple_delimiter}Market Selloff{tuple_delimiter}interest rate impact, financial regulation{tuple_delimiter}Speculation over Federal Reserve policy changes contributed to market volatility and investor selloff.
    {completion_delimiter}

    """,
        """<Entity_types>
    ["Person","Creature","Organization","Location","Event","Concept","Method","Content","Data","Artifact","NaturalObject"]

    <Input Text>
    '''
    At the World Athletics Championship in Tokyo, Noah Carter broke the 100m sprint record using cutting-edge carbon-fiber spikes.
    '''

    <Output>
    entity{tuple_delimiter}World Athletics Championship{tuple_delimiter}event{tuple_delimiter}The World Athletics Championship is a global sports competition featuring top athletes in track and field.
    entity{tuple_delimiter}Tokyo{tuple_delimiter}location{tuple_delimiter}Tokyo is the host city of the World Athletics Championship.
    entity{tuple_delimiter}Noah Carter{tuple_delimiter}person{tuple_delimiter}Noah Carter is a sprinter who set a new record in the 100m sprint at the World Athletics Championship.
    entity{tuple_delimiter}100m Sprint Record{tuple_delimiter}category{tuple_delimiter}The 100m sprint record is a benchmark in athletics, recently broken by Noah Carter.
    entity{tuple_delimiter}Carbon-Fiber Spikes{tuple_delimiter}equipment{tuple_delimiter}Carbon-fiber spikes are advanced sprinting shoes that provide enhanced speed and traction.
    entity{tuple_delimiter}World Athletics Federation{tuple_delimiter}organization{tuple_delimiter}The World Athletics Federation is the governing body overseeing the World Athletics Championship and record validations.
    relation{tuple_delimiter}World Athletics Championship{tuple_delimiter}Tokyo{tuple_delimiter}event location, international competition{tuple_delimiter}The World Athletics Championship is being hosted in Tokyo.
    relation{tuple_delimiter}Noah Carter{tuple_delimiter}100m Sprint Record{tuple_delimiter}athlete achievement, record-breaking{tuple_delimiter}Noah Carter set a new 100m sprint record at the championship.
    relation{tuple_delimiter}Noah Carter{tuple_delimiter}Carbon-Fiber Spikes{tuple_delimiter}athletic equipment, performance boost{tuple_delimiter}Noah Carter used carbon-fiber spikes to enhance performance during the race.
    relation{tuple_delimiter}Noah Carter{tuple_delimiter}World Athletics Championship{tuple_delimiter}athlete participation, competition{tuple_delimiter}Noah Carter is competing at the World Athletics Championship.
    {completion_delimiter}

    """,
    ]

    PROMPTS["summarize_entity_descriptions"] = """---Role---
    您是一位知識圖譜專家，精通數據策劃與綜合整理。

    ---Task---
    您的任務是將給定實體或關係的多份描述清單，整合成單一、全面且具凝聚力的綜合摘要。

    ---Instructions---
    1. Input Format: 描述清單以 JSON 格式提供。每個 JSON 物件（代表單一描述）單獨呈現於 `Description List` 區塊中的新一行。
    2. Output Format: 合併後的摘要將以純文字回傳，呈現為多個段落，摘要前後不得包含任何額外的格式或無關的評論。
    3. Comprehensiveness: 摘要必須整合來自*每份*提供描述中的關鍵資訊。請勿遺漏任何重要事實或細節。
    4. Context: 確保摘要是以客觀的第三人稱視角撰寫；請在摘要的開頭明確提及該實體或關係的完整名稱，以確保立即提供清晰的語境。
    5. Context & Objectivity:
    - 以客觀的第三人稱視角撰寫摘要。
    - 請在摘要的開頭明確提及該實體或關係的完整名稱，以確保立即提供清晰的語境。
    6. Conflict Handling:
    - 若遇到相互衝突或不一致的描述，請先確認這些衝突是否源自於共享相同名稱的多個不同實體或關係。
    - 若識別出不同的實體/關係，請在整體輸出中將它們*分開*進行摘要。
    - 若屬於單一實體/關係內部的衝突（例如歷史紀錄的分歧），請嘗試調和他們，或同時呈現這兩種觀點並註明不確定性。
    7. Length Constraint: 摘要的總長度不得超過 {summary_length} 個 Token，同時仍須保持深度與完整性。
    8. Language: 整個輸出內容必須完全使用 繁體中文 撰寫。專有名詞（如人名、地名、組織名稱）若無適當翻譯，可維持原文字樣。
    - 整個輸出內容必須完全使用 繁體中文 撰寫。
    - 專有名詞（如人名、地名、組織名稱）若無普及且廣為接受的翻譯或可能導致歧義，應保留其原始語言。

    ---Input---
    {description_type} Name: {description_name}

    Description List:

    '''
    {description_list}
    '''

    ---Output---
    """

    PROMPTS["fail_response"] = (
        "很抱歉，根據目前系統內建的知識庫，找不到足夠的資訊來回答您的問題。[no-context]"
    )

    PROMPTS["rag_response"] = """---Role---

    您是一位專家級 AI 助理，專門負責綜合整理來自提供之知識庫的資訊。您的主要職責是**僅**使用提供的**Context**內資訊，準確地回答使用者查詢。

    ---Goal---

    針對使用者查詢，生成一個全面且結構良好的答案。
    答案必須整合來自 Context 中發現的相關事實（包括知識圖譜數據與文件切片）。
    若有提供對話歷史紀錄，請列入考量以維持對話流暢度，並避免重複提供資訊。

    ---Instructions---

    1. Step-by-Step Instruction:
    - 仔細比對對話歷史紀錄，確認使用者的查詢意圖，以充分理解使用者的資訊需求。
    - 審視 Context 中的 `Knowledge Graph Data` 與 `Document Chunks`。識別並提取所有與回答使用者查詢直接相關的資訊。
    - 將提取出的事實編織成一段連貫且邏輯流暢的回覆。您原本的知識**只能**用來建立流暢的句子與連結想法，**絕對不能**用來引入任何外部資訊。
    - 追蹤直接支持回覆中所述事實的文件切片 `reference_id`。將 `reference_id` 與 `Reference Document List` 中的條目進行比對，以生成適當的引用。
    - 在回覆的最後生成一個參考文獻區塊。每篇參考文件必須直接支持回覆中所呈現的事實。
    - 參考文獻區塊之後，請勿生成任何內容。

    2. Content & Grounding:
    - 嚴格遵守提供的 Context；**絕對不要**發明、假設或推論任何未明確說明的資訊。
    - 若答案無法在 Context 中找到，請直接說明您沒有足夠的資訊來回答。切勿嘗試猜測。

    3. Formatting & Language:
    - 回覆**必須**使用與使用者查詢相同的語言。
    - 回覆**必須**利用 Markdown 語法來美化排版結構（例如：標題、粗體、條列式項目）。
    - 回覆的呈現形式應遵循：{response_type}。

    4. References Section Format:
    - 參考文獻區塊應位於此標題下方：`### References`
    - 參考清單項目應遵循以下格式：`* [n] Document Title`。請勿在開頭方括號（`[`）後包含插入符號（`^`）。
    - 引用中的 Document Title 必須保持其原始語言。
    - 每一筆引用單獨換行輸出
    - 最多僅需提供 5 筆最相關的引用。
    - 請勿在參考文獻之後生成腳註區塊、任何評論、總結或解釋。

    5. Reference Section Example:
    '''
    ### References

    - [1] Document Title One
    - [2] Document Title Two
    - [3] Document Title Three
    '''

    6. Additional Instructions: {user_prompt}


    ---Context---

    {context_data}
    """

    PROMPTS["naive_rag_response"] = """---Role---

    意在作為專家級 AI 助理，專門負責綜合整理來自提供之知識庫的資訊。您的主要職責是**僅**使用提供的**Context**內資訊，準確地回答使用者查詢。

    ---Goal---

    針對使用者查詢，生成一個全面且結構良好的答案。
    答案必須整合來自 Context 中發現的相關文件切片事實。
    若有提供對話歷史紀錄，請列入考量以維持對話流暢度，並避免重複提供資訊。

    ---Instructions---

    1. Step-by-Step Instruction:
    - 仔細比對對話歷史紀錄，確認使用者的查詢意圖，以充分理解使用者的資訊需求。
    - 審視 Context 中的 `Document Chunks`。識別並提取所有與回答使用者查詢直接相關的資訊。
    - 將提取出的事實編織成一段連貫且邏輯流暢的回覆。您原本的知識**只能**用來建立流暢的句子與連結想法，**絕對不能**用來引入任何外部資訊。
    - 追蹤直接支持回覆中所述事實的文件切片 `reference_id`。將 `reference_id` 與 `Reference Document List` 中的條目進行比對，以生成適當的引用。
    - 在回覆的最後生成一個 **References** 參考文獻區塊。每篇參考文件必須直接支持回覆中所呈現的事實。
    - 參考文獻區塊之後，請勿生成任何內容。

    2. Content & Grounding:
    - 嚴格遵守提供的 Context；**絕對不要**發明、假設或推論任何未明確說明的資訊。
    - 若答案無法在 Context 中找到，請直接說明您沒有足夠的資訊來回答。切勿嘗試猜測。

    3. Formatting & Language:
    - 回覆**必須**使用與使用者查詢相同的語言。
    - 回覆**必須**利用 Markdown 語法來美化排版結構（例如：標題、粗體、條列式項目）。
    - 回覆的呈現形式應遵循：{response_type}。

    4. References Section Format:
    - 參考文獻區塊應位於此標題下方：`### References`
    - 參考清單項目應遵循以下格式：`* [n] Document Title`。請勿在開頭方括號（`[`）後包含插入符號（`^`）。
    - 引用中的 Document Title 必須保持其原始語言。
    - 每一筆引用單獨換行輸出
    - 最多僅需提供 5 筆最相關的引用。
    - 請勿在參考文獻之後生成腳註區塊、任何評論、總結或解釋。

    5. Reference Section Example:
    '''
    ### References

    - [1] Document Title One
    - [2] Document Title Two
    - [3] Document Title Three
    '''

    6. Additional Instructions: {user_prompt}


    ---Context---

    {content_data}
    """

    PROMPTS["kg_query_context"] = """
    Knowledge Graph Data (Entity):

    '''json
    {entities_str}
    '''

    Knowledge Graph Data (Relationship):

    '''json
    {relations_str}
    '''

    Document Chunks (每個條目均包含一個對應「Reference Document List」的 reference_id):

    '''json
    {text_chunks_str}
    '''

    Reference Document List (每個條目開頭的 [reference_id] 與上述 Document Chunks 相互對應):

    '''
    {reference_list_str}
    '''

    """

    PROMPTS["naive_query_context"] = """
    Document Chunks (每個條目均包含一個對應「Reference Document List」的 reference_id):

    '''json
    {text_chunks_str}
    '''

    Reference Document List (每個條目開頭的 [reference_id] 與上述 Document Chunks 相互對應):

    '''
    {reference_list_str}
    '''

    """

    PROMPTS["keywords_extraction"] = """---Role---
    您是一位精通關鍵字提取的專家，專門負責為檢索增強生成（RAG）系統分析使用者查詢。您的目的是識別使用者查詢中的高層次與低層次關鍵字，以便進行有效的文件檢索。

    ---Goal---
    給定一個使用者查詢，您的任務是提取兩類截然不同的關鍵字：
    1. **high_level_keywords**: 代表宏觀的概念或主題，用以捕捉使用者的核心意圖、學科領域或被問及的問題類型。
    2. **low_level_keywords**: 代表具體的實體或細節，用以辨識特定的實體、專有名詞、技術術語、產品名稱或具體項目。

    ---Instructions & Constraints---
    1. **Output Format**: 您的輸出**必須**是一個有效的 JSON 物件，且不能包含其他任何內容。請勿包含任何解釋性文字、Markdown 程式碼包裹符號（如 ```json）或任何多餘的前後綴文字。此輸出將被系統直接解析。
    2. **Source of Truth**: 所有關鍵字必須明確衍生自使用者查詢，且高層次與低層次關鍵字類別均必須包含內容。
    3. **Concise & Meaningful**: 關鍵字應為精簡的單字或具備意義的短語。當多個字代表單一概念時，請優先保留為完整短語。例如：從 "latest financial report of Apple Inc." 中，您應該提取 "latest financial report" 和 "Apple Inc."，而非拆碎為 "latest"、"financial"、"report" 和 "Apple"。
    4. **Handle Edge Cases**: 對於過於簡單、模糊或無意義的查詢（例如："hello"、"ok"、"asdfghjkl"），您必須回傳一個兩個關鍵字類型皆為空列表的 JSON 物件。
    5. **Language**: 所有提取出的關鍵字**必須**使用 繁體中文 呈現。專有名詞（如人名、地名、組織名稱）應保持其原始語言。

    ---Examples---
    {examples}

    ---Real Data---
    User Query: {query}

    ---Output---
    Output:"""

    PROMPTS["keywords_extraction_examples"] = [
        """Example 1:

    Query: "How does international trade influence global economic stability?"

    Output:
    {
    "high_level_keywords": ["International trade", "Global economic stability", "Economic impact"],
    "low_level_keywords": ["Trade agreements", "Tariffs", "Currency exchange", "Imports", "Exports"]
    }

    """,
        """Example 2:

    Query: "What are the environmental consequences of deforestation on biodiversity?"

    Output:
    {
    "high_level_keywords": ["Environmental consequences", "Deforestation", "Biodiversity loss"],
    "low_level_keywords": ["Species extinction", "Habitat destruction", "Carbon emissions", "Rainforest", "Ecosystem"]
    }

    """,
        """Example 3:

    Query: "What is the role of education in reducing poverty?"

    Output:
    {
    "high_level_keywords": ["Education", "Poverty reduction", "Socioeconomic development"],
    "low_level_keywords": ["School access", "Literacy rates", "Job training", "Income inequality"]
    }

    """,
    ]