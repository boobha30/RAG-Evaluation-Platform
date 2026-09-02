pipeline {
    agent any

    environment {
        IMAGE_BACKEND = "rag-eval-backend"
        IMAGE_DASHBOARD = "rag-eval-dashboard"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Backend: install + test') {
            steps {
                sh '''
                    python3.10 -m venv .venv
                    . .venv/bin/activate
                    pip install --no-cache-dir -r requirements.txt
                    pytest tests/ -v --junitxml=reports/pytest.xml
                '''
            }
            post {
                always {
                    junit 'reports/pytest.xml'
                }
            }
        }

        stage('Dashboard: install + lint + typecheck + build') {
            steps {
                dir('dashboard') {
                    sh '''
                        npm ci
                        npx eslint .
                        npx tsc --noEmit
                        npm run build
                    '''
                }
            }
        }

        stage('Build Docker images') {
            steps {
                sh "docker build -t ${IMAGE_BACKEND}:${env.BUILD_NUMBER} -t ${IMAGE_BACKEND}:latest ."
                sh "docker build -t ${IMAGE_DASHBOARD}:${env.BUILD_NUMBER} -t ${IMAGE_DASHBOARD}:latest ./dashboard"
            }
        }

        // --- Everything below is documentation of the intended AWS deploy,
        // deliberately not wired to run automatically: it needs real AWS
        // credentials/account access and provisions billable resources.
        // Enable by adding an AWS credentials binding and uncommenting.
        /*
        stage('Push to ECR') {
            steps {
                withAWS(credentials: 'aws-creds', region: 'us-east-1') {
                    sh '''
                        aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
                        docker tag ${IMAGE_BACKEND}:latest $ECR_REGISTRY/${IMAGE_BACKEND}:latest
                        docker push $ECR_REGISTRY/${IMAGE_BACKEND}:latest
                        docker tag ${IMAGE_DASHBOARD}:latest $ECR_REGISTRY/${IMAGE_DASHBOARD}:latest
                        docker push $ECR_REGISTRY/${IMAGE_DASHBOARD}:latest
                    '''
                }
            }
        }

        stage('Deploy to ECS') {
            steps {
                withAWS(credentials: 'aws-creds', region: 'us-east-1') {
                    sh '''
                        aws ecs update-service --cluster rag-eval --service backend --force-new-deployment
                        aws ecs update-service --cluster rag-eval --service dashboard --force-new-deployment
                    '''
                }
            }
        }
        */
    }
}
