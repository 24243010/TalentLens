pipeline {
    agent any
    stages {
        stage('Build Docker Image') {
            steps {
                bat 'docker.exe build -t talentlens:test .'
            }
        }
        stage('Run Tests') {
            steps {
                bat 'docker.exe run --rm talentlens:test python -m pytest -v'
            }
        }
    }
}