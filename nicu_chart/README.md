# Neonatal ICU Chart (nicu_chart) — Odoo 19

موديول بيحوّل فورم **Neonatal ICU Chart – Patient I.D.** الورقي لأودو 19 بنفس الترتيب والصفوف والأقسام.

## التثبيت

### Odoo.sh
1. انسخ مجلد `nicu_chart` كما هو داخل الريبو بتاعك على GitHub (في جذر الريبو أو داخل أي مجلد addons مضاف للمشروع).
2. اعمل `git commit` و `git push` لفرع Staging أولاً وجرّب، بعدها اعمل Merge لفرع Production.
3. من **Apps** ← Update Apps List ← ابحث عن `Neonatal ICU Chart` ← Install.

### On-Premise
1. انسخ مجلد `nicu_chart` داخل مجلد custom addons، مثلاً `/opt/odoo/custom-addons/nicu_chart`.
2. تأكد إن المسار موجود في `addons_path` داخل `odoo.conf`.
3. أعد تشغيل خدمة أودو، بعدها Apps ← Update Apps List ← Install.
   أو من الطرفية: `odoo-bin -c odoo.conf -d <db> -i nicu_chart`
4. الطباعة PDF تحتاج **wkhtmltopdf 0.12.6 (with patched qt)** زي أي تقرير في أودو.

## الصلاحيات
من Settings ← Users، في قسم **Neonatal ICU** اختار:
* **Nurse / Doctor**: يضيف ويعدّل الشارتات، وما بيقدر يمسحها.
* **Administrator**: صلاحية كاملة.

## طريقة الشغل
* أول حاجة سجّل الطفل من **Neonatal ICU ← Patients** (MRN، تاريخ الميلاد، عمر الحمل، وزن الولادة، فصيلة الدم).
* اعمل **شارت واحد لكل طفل في كل يوم** من **Neonatal ICU ← ICU Charts**.
* الشاشة مقسمة زي الورقة:
  * Patient I.D. فوق الشاشة.
  * Nursing Care & Vital Signs: الرسم البياني للعلامات الحيوية بيترسم تلقائياً. اكتب الضغط بالصيغة `60/35(45)`.
  * Ventilation / Respiratory.
  * IV / Medications / Blood Products.
  * Physical Assessment (Day / Night).
  * Progress Evaluation.
* صفوف TOTAL و TOTAL INTAKE و TOTAL URINE و URINE OUTPUT (ml/kg/hr) و TOTAL OUTPUT و FLUID BALANCE وملخص الـ24 ساعة بتتحسب تلقائياً بعد الحفظ.
* زر **Next Day Chart** بيفتح شارت اليوم التالي، وبينقل التشخيص والاستشاري وحدود الإنذارات وأسماء المحاليل والقساطر، والوزن الحالي بيبقى هو الوزن السابق.
* زر **Print Chart** بيطلع PDF مقاس A3 أفقي بنفس تصميم الورقة (وجهين).
* لوقو المستشفى في الطباعة بيتاخد من شعار الشركة في الإعدادات.

## بيانات تجريبية (Sample)
* لو قاعدة البيانات فيها Demo Data، الشارت التجريبي بيتعمل تلقائياً مع التثبيت.
* في أي قاعدة بيانات (حتى Production / Staging بدون Demo): **Neonatal ICU ← Configuration ← Load Sample Chart**.
  بيعمل طفل اسمه `Baby Sample (Demo)` (MRN: DEMO-0001) مع شارت أمس واليوم مليانين، وبيفتح شارت اليوم مباشرة.
  الزر بيظهر لمجموعة Administrator بس. البيانات وهمية، وتقدر تمسحها بعد التجربة.
