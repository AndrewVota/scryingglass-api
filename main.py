import cv2 as cv
import numpy as np
from fastapi import FastAPI, File, UploadFile
import psycopg2
import os
from dotenv import find_dotenv, load_dotenv
from CardDetector import detect
app = FastAPI()

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

DB_NAME = os.getenv("DATABASE")
DB_USER = os.getenv("USER")
DB_PASSWORD = os.getenv("PASSWORD")
DB_HOST = os.getenv("HOST")
DB_PORT = os.getenv("PORT")

db_connection = psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
db_cursor = db_connection.cursor()

@app.post("/scry")
async def UploadImage(file: UploadFile = File(...)):
    content = await file.read()
    im_file = np.asarray(bytearray(content), dtype=np.uint8)
    img = cv.imdecode((im_file), cv.IMREAD_UNCHANGED)

    original_hash_int, processed_hash_otsu_int, processed_hash_binary_otsu_int, processed_hash_binary_int, processed_hash_adaptive_int = detect(img)

    db_cursor.execute("SELECT scryfall_uri, perceptual_hash_int FROM cards ORDER BY ABS(perceptual_hash_int - %s) ASC LIMIT 1", ([original_hash_int]))
    original_scryfall_uri, original_p_hash_int = db_cursor.fetchone()
    
    db_cursor.execute("SELECT scryfall_uri, perceptual_hash_int FROM cards ORDER BY ABS(perceptual_hash_int - %s) ASC LIMIT 1", ([processed_hash_otsu_int]))
    processed_otsu_scryfall_uri, processed_otsu_p_hash_int = db_cursor.fetchone()

    db_cursor.execute("SELECT scryfall_uri, perceptual_hash_int FROM cards ORDER BY ABS(perceptual_hash_int - %s) ASC LIMIT 1", ([processed_hash_binary_otsu_int]))
    processed_binary_otsu_scryfall_uri, processed_binary_otsu_p_hash_int = db_cursor.fetchone()

    db_cursor.execute("SELECT scryfall_uri, perceptual_hash_int FROM cards ORDER BY ABS(perceptual_hash_int - %s) ASC LIMIT 1", ([processed_hash_binary_int]))
    processed_binary_scryfall_uri, processed_binary_p_hash_int = db_cursor.fetchone()

    db_cursor.execute("SELECT scryfall_uri, perceptual_hash_int FROM cards ORDER BY ABS(perceptual_hash_int - %s) ASC LIMIT 1", ([processed_hash_adaptive_int]))
    processed_adaptive_scryfall_uri, processed_adaptive_p_hash_int = db_cursor.fetchone()

    
    original_hamming_distance = abs(original_hash_int - original_p_hash_int)
    processed_otsu_hamming_distance = abs(processed_hash_otsu_int - processed_otsu_p_hash_int)
    processed_binary_otsu_hamming_distance = abs(processed_hash_binary_otsu_int - processed_binary_otsu_p_hash_int)
    processed_binary_hamming_distance = abs(processed_hash_binary_int - processed_binary_p_hash_int)
    processed_adaptive_hamming_distance = abs(processed_hash_adaptive_int - processed_adaptive_p_hash_int)


    data = {
        'original': {
            'scryfall_uri': original_scryfall_uri,
            'hamming_distance': original_hamming_distance
        },
        'otsu': {
            'scryfall_uri': processed_otsu_scryfall_uri,
            'hamming_distance': processed_otsu_hamming_distance
        },
        'binary_otsu': {
            'scryfall_uri': processed_binary_otsu_scryfall_uri,
            'hamming_distance': processed_binary_otsu_hamming_distance
        },
        'binary': {
            'scryfall_uri': processed_binary_scryfall_uri,
            'hamming_distance': processed_binary_hamming_distance
        },
        'adaptive': {
            'scryfall_uri': processed_adaptive_scryfall_uri,
            'hamming_distance': processed_adaptive_hamming_distance
        }
    }

    min_distance = min(data, key=lambda x: data[x]['hamming_distance'])
    return {'uri': data[min_distance]['scryfall_uri']}