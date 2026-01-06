# AI Testing Guide - Liver Pathology Analysis

This guide explains how to use the new AI testing feature to evaluate the accuracy of DiagnoseAI's image analysis capabilities.

## 🎯 Purpose

Test the AI's ability to analyze liver ultrasound images and identify pathologies without any patient context or clinical information. This helps evaluate:

- **Accuracy**: How well does the AI identify the correct pathology?
- **Completeness**: Does the AI provide comprehensive findings?
- **Medical Terminology**: Does the AI use appropriate medical language?
- **Consistency**: How consistent are the results across similar cases?

## 🚀 How to Use

### Method 1: Web Interface (Single Images)

1. **Access the AI Testing Page**
   - Login to DiagnoseAI
   - Click "AI Testing" in the navigation menu
   - Or use the "AI Testing" button on the dashboard

2. **Upload and Analyze**
   - Select an ultrasound image file
   - Optionally specify the view type (Left Lobe TR, Portal Vein, etc.)
   - Add any additional context if needed
   - Click "Analyze Image with AI"

3. **Review Results**
   - View the AI's detailed analysis
   - Rate the performance using the evaluation form
   - Export results for further analysis
   - Test another image or return to dashboard

### Method 2: Batch Testing (Multiple Images)

For testing your entire liver pathology folder:

```bash
# Navigate to DiagnoseAI directory
cd /Users/abdullahwaheed/Downloads/radiology-ai-application/DiagnoseAI

# Activate virtual environment
source venv/bin/activate

# Run batch testing
python batch_ai_test.py /path/to/your/liver_pathology_folder
```

## 📁 Expected Folder Structure

Your liver pathology folder should be organized as:

```
liver_pathology/
├── left lobe tr view/
│   ├── Dilated hepatic veins - Passive heaptic congestion.jpg
│   ├── Coarse Liver 2.jpg
│   ├── Left Lobe TR .jpg
│   └── Multiple hepatic cysts.jpg
├── portal vein view/
│   ├── Cavernuos transformation Grey scale.jpg
│   ├── Cavernuos transformation.jpg
│   ├── Dilated PV.jpg
│   ├── PORTAL VEIN VIEW NORMAL.jpg
│   └── PV Thrumbus.jpg
└── right lobe log view/
    ├── Ascities.jpg
    ├── COARSE lLIVER.jpg
    ├── Fatty liver.jpg
    ├── Hemengioma.jpg
    ├── Hepatic abscess.jpg
    ├── Hepatic edema - Acute hepatitis.jpg
    ├── Hepatic simple cyst.jpg
    ├── Hepatic Soft tissue mass.jpg
    ├── liver size jp.png
    ├── Metastatic focal nodule.jpg
    └── Pleural effusion.jpg
```

## 📊 Expected Pathologies

### Left Lobe TR View
- Dilated hepatic veins
- Passive hepatic congestion  
- Coarse liver texture
- Multiple hepatic cysts

### Portal Vein View
- Cavernous transformation
- Dilated portal vein
- Portal vein thrombosis
- Normal portal vein

### Right Lobe Log View
- Ascites
- Fatty liver
- Hemangioma
- Hepatic abscess
- Hepatic edema
- Acute hepatitis
- Simple hepatic cyst
- Soft tissue mass
- Metastatic focal nodule
- Pleural effusion

## 🔍 Evaluation Criteria

When rating the AI's performance, consider:

### Accuracy (1-5 stars)
- Did the AI correctly identify the main pathology?
- Are the findings consistent with the expected diagnosis?
- How many false positives/negatives?

### Completeness (1-5 stars)
- Did the AI describe all visible abnormalities?
- Were important anatomical structures mentioned?
- Was the assessment comprehensive?

### Medical Terminology (1-5 stars)
- Did the AI use appropriate medical terms?
- Was the language professional and precise?
- Were abbreviations used correctly?

### Overall Rating (1-5 stars)
- Would you trust this analysis in a clinical setting?
- How helpful would this be as a preliminary report?
- Overall quality and usefulness?

## 📈 Results Analysis

### Individual Test Results
- View detailed AI analysis
- Compare with expected pathology
- Rate performance across multiple criteria
- Export results as JSON for further analysis

### Batch Test Results
- Comprehensive JSON report with all analyses
- Success rate statistics by folder/view type
- Individual image results with timestamps
- Error tracking and analysis

### Sample Batch Results Structure
```json
{
  "test_date": "2026-01-06T...",
  "total_images": 18,
  "successful_analyses": 16,
  "failed_analyses": 2,
  "summary": {
    "success_rate_percent": 88.89
  },
  "results_by_folder": {
    "left lobe tr view": {
      "success_count": 4,
      "error_count": 0,
      "images": [...]
    }
  }
}
```

## 🛠 Troubleshooting

### Common Issues

**AI Analysis Fails**
- Check OpenAI API key in .env file
- Ensure image file is valid and not corrupted
- Verify image format is supported (JPG, PNG, etc.)

**Batch Script Errors**
- Ensure virtual environment is activated
- Check folder path exists and is accessible
- Verify image files have proper extensions

**Poor AI Performance**
- Check image quality and clarity
- Ensure proper ultrasound image orientation
- Consider adding more context in the form

### Getting Help

1. Check the application logs for detailed error messages
2. Verify all dependencies are installed correctly
3. Test with a single image first before batch processing
4. Ensure OpenAI API key has sufficient credits

## 📝 Best Practices

1. **Start Small**: Test a few images manually before running batch analysis
2. **Document Results**: Keep track of which pathologies the AI handles well/poorly
3. **Consistent Naming**: Use descriptive filenames that indicate the expected pathology
4. **Quality Images**: Use clear, well-oriented ultrasound images for best results
5. **Regular Testing**: Test periodically to track AI performance improvements

## 🎯 Success Metrics

Track these metrics to evaluate AI performance:

- **Overall Accuracy**: % of correctly identified pathologies
- **Sensitivity**: % of actual pathologies correctly identified
- **Specificity**: % of normal cases correctly identified as normal
- **Clinical Utility**: How helpful the AI analysis would be to radiologists

## 📞 Support

For issues or questions about AI testing:
- Check the LOCAL_SETUP.md for basic troubleshooting
- Review application logs for detailed error information
- Test with known good images to isolate issues