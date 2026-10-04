pipeline {
  agent any
  environment { IMAGE = "YOUR_DOCKERHUB_USERNAME/resume-analyzer" }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Test') {
      steps {
        sh 'python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt pytest && pytest -q tests'
      }
    }
    stage('Build Image') {
      steps { sh 'docker build -t $IMAGE:$BUILD_NUMBER -t $IMAGE:latest .' }
    }
    stage('Push to Docker Hub') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                         usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
          sh 'echo $DH_PASS | docker login -u $DH_USER --password-stdin'
          sh 'docker push $IMAGE:$BUILD_NUMBER'
          sh 'docker push $IMAGE:latest'
        }
      }
    }
  }
  post { always { sh 'docker logout || true' } }
}
