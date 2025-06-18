from model.predict_disease import predict_disease

image_path = "test_images/sample.jpg"
result = predict_disease(image_path)
print("✅ Predicted Disease:", result)
