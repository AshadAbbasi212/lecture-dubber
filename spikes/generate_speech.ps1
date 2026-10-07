Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile("spikes\test_data\speech_sample.wav")
$synth.Speak("Welcome to the lecture on artificial intelligence and neural networks. Today we will explore how machine learning models process spoken language and translate complex technical terminology across different languages.")
$synth.Dispose()
Write-Host "Generated speech_sample.wav successfully"
