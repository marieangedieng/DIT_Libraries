pipeline {
  agent any

  environment {
    PYTHON = 'python3'
  }

  stages {
    stage('Préparation') {
      steps {
        sh '''
          $PYTHON -m venv .venv
          . .venv/bin/activate
          pip install --upgrade pip
          pip install -r services/livres/requirements.txt
          pip install -r services/utilisateurs/requirements.txt
          pip install -r services/emprunts/requirements.txt
          pip install -r services/statistiques/requirements.txt
          pip install -r services/recommandation/requirements.txt
        '''
      }
    }

    stage('Pipeline DVC') {
      steps {
        sh '''
          . .venv/bin/activate
          python scripts/preprocess.py
          python scripts/train.py
          python scripts/evaluate.py
        '''
      }
    }

    stage('Build Docker') {
      steps {
        sh 'docker compose --profile prod build'
      }
    }
  }
}
