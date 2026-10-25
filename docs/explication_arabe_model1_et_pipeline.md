# شرح مشروع NewsCheck TN ودور Lot C / Model 1

> هذا الملف يشرح ما أُنجز في Model 1، وما الذي يفعله ولا يفعله، وكيف يدخل
> ضمن بقية أدوار مشروع NewsCheck TN للوصول في النهاية إلى خبر مدعوم أو خاطئ
> أو مضلّل أو أدلته غير كافية.

## 1. ما هي فكرة المشروع؟

NewsCheck TN هو نظام مساعد للتحقق من الأخبار والنصوص بالفرنسية والعربية
والتونسية (بالحروف العربية أو Arabizi مثل `9al` و`bech`). لا يجوز أن يعطي
النظام حكماً من غير دليل. لذلك يقسم العمل إلى مراحل، وكل Lot مسؤول عن مرحلة
واضحة.

الهدف النهائي ليس أن يقول النموذج وحده «هذا الخبر صحيح» بمجرد قراءة جملة.
الهدف هو:

1. إيجاد الجمل التي يمكن التحقق منها.
2. البحث عن مصادر أو مقاطع أدلة ذات صلة.
3. مقارنة الادعاء بالدليل.
4. إنتاج حكم واضح ومبرر بالمصادر.

المسار الكامل هو:

```text
نص خام من المستخدم
     │
     ▼
[Lot A2] تنظيف النص وتحديد اللغة
     │
     ▼
[Lot B] استخراج الجمل التي تبدو كادعاءات
     │
     ▼
[Lot C / Model 1] هل الجملة ادعاء قابل للتحقق؟
     │                         │
     │                    لا → لا نرسلها للتحقق
     ▼
[Lot A1 + Lot D] البحث عن أدلة ومصادر مرتبطة بها
     │
     ▼
[Lot C / Model 2] هل الدليل يؤيد الادعاء أو ينفيه أو لا يكفي؟
     │
     ▼
[Lot D] verdict نهائي مع citation ودرجة عدم يقين
     │
     ▼
[Lot E] API والواجهة التي يراها المستخدم
```

## 2. السؤال الأهم: هل Model 1 يقول إن الخبر صحيح أو خاطئ؟

**لا.** هذه أهم نقطة في المشروع.

Model 1 يسأل سؤالاً واحداً فقط:

> هل هذه الجملة تحتوي على معلومة واقعية يمكن البحث عنها والتحقق منها بمصادر؟

ولا يسأل:

> هل المعلومة صحيحة فعلاً؟

مثال:

```text
«نسبة البطالة في تونس بلغت 80% سنة 2024.»
```

هذه الجملة قد تكون خاطئة جداً، لكنّها تبقى **AFFIRMATION** لأننا نستطيع فتح
مصدر رسمي أو تقرير إحصائي والتحقق من الرقم والسنة. لذلك Model 1 يمررها إلى
الخطوات التالية؛ لا يرفضها بسبب أنها قد تكون كاذبة.

في المقابل:

```text
«هذه أسوأ حكومة في التاريخ.»
```

هي **OPINION**: رأي أو حكم شخصي، ولا يوجد دليل واحد يستطيع إثباته أو نفيه
بشكل موضوعي. لا يحتاج النظام إلى إرسالها إلى محرك التحقق.

ومثال ثالث:

```text
«هل سترتفع الأسعار؟»
```

هي **AUTRE** لأنها سؤال، لا ادعاء يقدّم حقيقة.

إذن Model 1 هو **بوابة أو فلتر أول**. فائدته أنه يمنع تضييع الوقت والبحث في
الأسئلة والتحيات والآراء، ويعطي الأولوية للادعاءات التي تستحق التحقق.

## 3. التصنيفات التي تعلّمها Model 1

التصنيف فيه ثلاث فئات:

| الفئة | معناها | مثال |
| --- | --- | --- |
| `AFFIRMATION` | معلومة قابلة للتحقق من مصادر | «قالت الوزارة إن الأسعار ارتفعت في 2024.» |
| `OPINION` | رأي أو تقييم شخصي | «القرار ظالم وغير منطقي.» |
| `AUTRE` | سؤال، تمنٍّ، تحية، فرضية، أو جزء غير كامل | «إن شاء الله تتحسن الأوضاع.» |

نحتفظ كذلك بـ`modalité` من Lot B. أمثلة عليها:

| Modalité | مثال | هل قد تبقى AFFIRMATION؟ |
| --- | --- | --- |
| `assertif` | «الأسعار ارتفعت.» | نعم |
| `rapporté` | «قال الوزير إن الأسعار ارتفعت.» | نعم |
| `conditionnel` | «البنك قد يرفع الفائدة.» | نعم، لأنها معلومة صحفية قابلة للفحص |
| `interrogatif` | «هل ارتفعت الأسعار؟» | لا، عادة AUTRE |
| `souhait` | «نأمل أن تنخفض الأسعار.» | لا، عادة AUTRE |
| `hypothétique` | «إذا استمر الجفاف...» | لا، عادة AUTRE |

الجملة المنقولة مثل «قال الوزير إن...» ليست بالضرورة صحيحة، لكنها ادعاء يمكن
فحصه: إما نتحقق هل قال الوزير ذلك، أو نتحقق من المعلومة المنقولة نفسها.

## 4. البيانات التي استعملناها

استعملنا ملفاً أصلياً فيه **600 جملة معنونة**. كل سطر يحتوي على:

```json
{
  "id": "...",
  "text": "النص الأصلي",
  "label": "AFFIRMATION | OPINION | AUTRE",
  "modalite": "...",
  "lang": "fr | ar | tn"
}
```

توزيع الفئات:

| الفئة | العدد |
| --- | ---: |
| AFFIRMATION | 316 |
| AUTRE | 191 |
| OPINION | 93 |
| **المجموع** | **600** |

وتوزيع اللغات:

| اللغة | العدد |
| --- | ---: |
| تونسي `tn` | 290 |
| فرنسي `fr` | 160 |
| عربي فصيح `ar` | 150 |

يوجد test ثابت من **120 جملة**. هذا الـtest لا يدخل أبداً في training. تبقى
480 جملة، منها 408 للتدريب و72 للـvalidation في كل run.

```text
600
├── 120 test gelé: قياس نهائي فقط
└── 480
    ├── 408 train: يتعلم منها النموذج
    └── 72 validation: نختار بها أفضل epoch
```

سبب تثبيت test هو المقارنة العادلة: TF-IDF وMiniLM وXLM-R يرون الجمل نفسها
وقت التقييم.

## 5. ما الذي أنجزناه خطوة بخطوة؟

### 5.1 تجهيز البيانات

كتبنا script يحول البيانات إلى الملف الموحد:

```text
data/prepare_claim_detection_dataset.py
data/processed/claim_detection_600.jsonl
```

كما راجعنا metadata اللغة لـ60 جملة كانت `unk`. لم نغيّر النصوص أو labels
الأصلية؛ أضفنا فقط لغة مناسبة حتى نحسب النتائج FR / AR / TN بشكل صحيح.

### 5.2 Baseline classique: TF-IDF + Logistic Regression

هذه أول baseline بسيطة، وليست Transformer.

- **TF-IDF** يحوّل النص إلى أرقام حسب مقاطع الحروف (character n-grams من 3
  إلى 5).
- **Logistic Regression** تتعلم قرار الفئة من هذه الأرقام.

اخترنا مقاطع الحروف لأنّها مناسبة للتونسي وArabizi والأخطاء الكتابية، مثلاً
`9al` أو اختلاف كتابة الكلمة. النتيجة:

```text
Macro-F1 = 0.6435
```

اسم الملف:

```text
models/baselines/claim_detection_multiclass_tfidf.py
```

### 5.3 Baseline neuronale: MiniLM embeddings + Logistic Regression

المطلوب في التقييم كان baseline عصبية أيضاً. استعملنا نموذجاً متعدد اللغات
اسمه `paraphrase-multilingual-MiniLM-L12-v2` كي يحول كل جملة إلى embedding
(تمثيل رقمي يحمل بعض المعنى). أبقيناه **مجمداً**، أي لم ندرّبه من جديد، ثم
استعملنا Logistic Regression للتصنيف.

النتيجة:

```text
Macro-F1 = 0.6350
```

هي أقل قليلاً من TF-IDF على كامل test. لكنها baseline مهمة لأنها تبيّن أن
وجود embeddings فقط لا يكفي؛ fine-tuning المخصص قد يفيد أكثر.

الملف:

```text
models/baselines/claim_detection_embedding_logreg.py
```

### 5.4 النموذج الرئيسي: XLM-R + LoRA

النموذج المختار هو:

```text
FacebookAI/xlm-roberta-base
```

وهو Transformer متعدد اللغات، يفهم سياقاً أكثر من TF-IDF. يستطيع مثلاً أن
يتعلم الفرق بين `si`, `ken`, `إذا` وبين جملة تقريرية مباشرة.

لكن XLM-R كبير، والبيانات 600 جملة فقط. لذلك استعملنا:

- **PEFT**: تدريب فعّال في استهلاك الذاكرة.
- **LoRA**: نجمّد معظم XLM-R ونضيف matrices صغيرة قابلة للتعلم داخل attention.

المعنى العملي: لا نعيد تدريب كل النموذج الضخم، بل ندرّب جزءاً صغيراً موجهاً
لهذه المهمة. هذا يناسب GPU Tesla T4 وبيانات صغيرة، ويقلل خطر overfitting.

أهم الإعدادات:

| الإعداد | القيمة |
| --- | ---: |
| base model | `xlm-roberta-base` |
| عدد الفئات | 3 |
| LoRA rank | 8 |
| LoRA alpha | 16 |
| LoRA dropout | 0.1 |
| target modules | `query`, `value` |
| max length | 256 tokens |
| learning rate | `2e-4` |
| batch size | 8 |
| أقصى epochs | 8 |

ملف التدريب:

```text
models/encoders/train_xlmr_claim_detection.py
```

### 5.5 لماذا شغّلنا 3 seeds؟

`seed` رقم يثبت العشوائية. لا يغير البيانات ولا model architecture ولا
hyperparameters. لكنه يغير بطريقة مضبوطة:

1. ترتيب أمثلة التدريب؛
2. البداية العشوائية لـLoRA؛
3. التقسيم الداخلي 408 train / 72 validation.

لذلك شغلنا نفس التجربة بـ42 و123 و2026:

| seed | Macro-F1 XLM-R |
| --- | ---: |
| 42 | 0.7108 |
| 123 | 0.7715 |
| 2026 | 0.7250 |
| **المتوسط ± الانحراف المعياري** | **0.7357 ± 0.0317** |

لا نختار seed123 للـAPI فقط لأنه الأفضل بعد رؤية test؛ هذا يسمى selection
bias. استعملنا checkpoint `seed42` كمرجع ثابت للـAPI، بينما الرقم العلمي
الذي نعرضه هو متوسط seeds الثلاثة.

### 5.6 النتائج حسب اللغة

| النموذج | Global | FR | AR | TN |
| --- | ---: | ---: | ---: | ---: |
| TF-IDF + LR | 0.6435 | 0.5760 | 0.4778 | 0.6846 |
| MiniLM figé + LR | 0.6350 | 0.8228 | 0.8002 | 0.4886 |
| XLM-R + LoRA | **0.7357 ± 0.0317** | **0.9148** | **0.6882 ± 0.0185** | **0.6863 ± 0.0567** |

هذه الأرقام Macro-F1. لا نبالغ في تفسيرها لأن test لكل لغة صغير، خصوصاً FR
فيه 26 جملة وAR فيه 30 جملة.

### 5.7 Bootstrap: هل تحسن XLM-R مؤكّد إحصائياً؟

الفرق بين XLM-R seed42 وTF-IDF هو:

```text
0.7108 - 0.6435 = +0.0673
```

عملنا paired bootstrap 1000 مرة: نعيد اختيار نفس جمل test مع replacement
ونحسب الفرق بين النموذجين في كل مرة.

```text
IC 95% = [-0.0468 ; 0.1860]
p-value = 0.254
```

لأن interval يحتوي الصفر وp أكبر من 0.05، لا نقول إن XLM-R «أفضل بشكل مؤكد
إحصائياً» على 120 جملة فقط. نقول بأمانة: تحسن مرصود، لكنه غير حاسم إحصائياً
مع حجم test الحالي.

### 5.8 Ablation: raw أم normalized؟

سؤال مهم: هل ندرب Model 1 على النص الخام أم على النص بعد normalisation A2؟

| طريقة النص | Macro-F1 seed42 |
| --- | ---: |
| raw | 0.7108 |
| normalized | 0.6671 |

النسخة raw أفضل بـ0.0436. الفرق ليس significant إحصائياً (p = 0.188)، لكن
الـnormalisation خفّضت نتيجة التونسي والعربي. لذلك احتفظنا بـraw لتصنيف
Model 1.

## 6. مشكلة مهمة أصلحناها: التدريب والـAPI

في البداية كان XLM-R متدرّباً على `raw`، لكن الـAPI كانت تعمل normalisation
قبل إرساله إلى Model 1. هذا يسمى **mismatch**: model يرى في production نصاً
مختلفاً عن النص الذي تعلّم عليه.

أصلحنا هذا في:

```text
pipeline.py
api/main.py
models/claim_detector.py
```

الآن يحصل التالي:

```text
النص الأصلي
  ├── نسخة normalisée → Lot B + retrieval + NLI
  └── نسخة raw        → XLM-R Model 1 فقط
```

الجملة التي تظهر في output تبقى normalisée كي تستعملها المراحل اللاحقة، لكن
XLM-R يتخذ قرار `AFFIRMATION / OPINION / AUTRE` من الجملة الخام المطابقة.
إذا اختلف تقطيع الجمل بين النسختين، يوجد fallback آمن إلى normalisé بدلاً من
ربط جملتين غير متطابقتين.

اختبرنا API فعلياً عبر Swagger:

```text
POST /extract  → 200
POST /check    → 200
```

مثال تونسي:

```text
El wizir 9al elli les prix bech yzidou fi 2025.
```

أعطى النظام:

```text
lang = tn
modalité = rapporté
checkworthiness = 0.9939
```

هذا لا يعني أن الأسعار سترتفع حتماً؛ معناه فقط أن الجملة ادعاء جدير بالتحقق.

## 7. كيف نعرف في النهاية الخبر صحيح أم خطأ؟

هنا يدخل **Model 2**. Model 1 لا يكفي وحده.

بعد أن يمرر Model 1 claim، يقوم Lot D بالبحث في corpus الذي أعدّه Lot A1:

```text
Claim: «الوزارة قالت إن الأسعار ارتفعت 10% في 2024.»
                │
                ▼
بحث في articles / Tunifact / passages موثقة
                │
                ▼
Evidence: «أفاد المعهد ... أن الأسعار ارتفعت 8% سنة 2024.»
```

ثم Model 2، وهو **NLI = Natural Language Inference**، يأخذ زوجاً:

```json
{
  "claim": "الأسعار ارتفعت 10% في 2024.",
  "evidence": "الأسعار ارتفعت 8% سنة 2024."
}
```

ويعطي واحدة من ثلاث فئات:

| نتيجة Model 2 | معناها |
| --- | --- |
| `supports` | الدليل وحده يؤيد الادعاء |
| `refutes` | الدليل وحده يناقض الادعاء |
| `neutral` | نفس الموضوع تقريباً لكن لا يكفي للحكم |

في المثال، دليل يقول 8% لا يؤيد ادعاء 10%، لذلك غالباً يكون `refutes` أو على
الأقل لا يكفي حسب صياغة الدليل.

بعد ذلك Lot D يجمع نتائج الأدلة ويعطي verdict على مستوى claim:

| Verdict النهائي | متى نستعمله؟ |
| --- | --- |
| `vrai` | أدلة موثوقة تدعم الادعاء بوضوح |
| `faux` | أدلة موثوقة تناقضه بوضوح |
| `trompeur` | فيه جزء صحيح لكن السياق أو الرقم أو الصياغة مضللة |
| `preuves_insuffisantes` | لا توجد أدلة كافية أو الأدلة لا تحسم |

إذن الحكم الصحيح/الخاطئ لا يأتي من Model 1 ولا من Model 2 وحده فقط. يأتي من
**الدليل الحقيقي + مقارنة NLI + قواعد verdict**.

## 8. أين وصل Model 2 الآن؟

Model 2 يحتاج dataset مختلفاً عن Model 1. لا نضع له 600 جملة منفردة، بل نحتاج
أزواجاً معلّمة من الشكل:

```json
{
  "pair_id": "...",
  "claim": "...",
  "evidence": "...",
  "label": "supports | refutes | neutral"
}
```

هذه البيانات يجب أن تأتي من Lot A1 / corpus الأدلة مع annotation بشري مستقل.
ينتظر Model 2 هذه الأزواج قبل fine-tuning. لذلك لا يجوز الادعاء اليوم أن
النظام ML يحكم نهائياً على صحة الخبر؛ Model 1 مكتمل، أما Model 2 يحتاج data
NLI الصحيحة أولاً.

## 9. دور كل Lot باختصار

| Lot | الدور | ما يرسل للمرحلة التالية |
| --- | --- | --- |
| A1 | جمع corpus، provenance، بيانات الأدلة، وpairs NLI | passages موثقة + claims/evidence labels |
| A2 | normalisation وتحديد اللغة | `Document(raw_text, text, lang)` |
| B | تقطيع واستخراج claim وSPO وmodalité | `Claim` candidates |
| C / Model 1 | فلترة AFFIRMATION / OPINION / AUTRE | claims قابلة للتحقق + score |
| C / Model 2 | NLI بين claim وevidence | supports / refutes / neutral |
| D | retrieval وverdict مع citations | vrai / faux / trompeur / preuves insuffisantes |
| E | API، frontend، وتجميع pipeline | تجربة واحدة للمستخدم |

## 10. الملفات المهمة التي أنشأناها أو عدلناها

```text
data/prepare_claim_detection_dataset.py
data/processed/claim_detection_600.jsonl
data/splits/claim_detection_multiclass_600_seed42.json

models/baselines/claim_detection_multiclass_tfidf.py
models/baselines/claim_detection_embedding_logreg.py
models/encoders/train_xlmr_claim_detection.py
models/encoders/evaluate_claim_detection.py
models/evaluation/bootstrap_paired_macro_f1.py
models/evaluation/error_stability.py
models/evaluation/summarize_model1_results.py
models/evaluation/capture_environment.py
models/claim_detector.py

pipeline.py
api/main.py

docs/model1_claim_detection_detailed_report.md
docs/model1_reproducibility.md
models/model_cards/claim_detection_xlmr_lora.md
experiments.md
```

## 11. نتائج Model 1 النهائية التي يمكن قولها في العرض

يمكن قول الآتي بأمانة:

> أنجزنا Model 1 للكشف عن الادعاءات القابلة للتحقق بثلاث فئات
> AFFIRMATION / OPINION / AUTRE. قارنا TF-IDF وMiniLM وXLM-R + LoRA على test
> ثابت من 120 جملة بثلاث seeds. XLM-R حقق أفضل متوسط Macro-F1 = 0.7357 ±
> 0.0317. دمجناه في API واختبرنا extraction وpipeline الكامل. النموذج لا
> يحكم على صدق الخبر؛ دوره تمرير الادعاءات إلى retrieval ثم Model 2 NLI الذي
> يقارنها بأدلة حقيقية. الحكم النهائي vrai/faux/trompeur/preuves insuffisantes
> يصدر بعد الأدلة، لا قبلها.

## 12. ما المتبقي؟

1. الحصول على بيانات NLI المعلّمة من Lot A1: claim + evidence + supports / refutes / neutral.
2. تدريب وتقييم Model 2 على هذه الأزواج.
3. عند الحاجة لتوثيق training time بدقة، إعادة runs XLM-R الثلاثة بالـscript
   الحالي؛ فهو يسجل `training_seconds` تلقائياً. لا نخترع وقتاً للruns القديمة.
4. تحسين حجم البيانات، خاصة OPINION والتونسي، لأنّهما أصعب الحالات.
