# package: fastapi, bcrypt, sqlalchemy, python-jose

# test lokal uvicorn main:app --host 0.0.0.0 --port 8000 --reload --


# kalau deploy di server: pip install gunicorn
# gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --daemon
# mematikan gunicorn (saat mau update):
# ps ax|grep gunicorn 
# pkill gunicorn



import uuid
from fastapi import Depends, Request, FastAPI, HTTPException, UploadFile

from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session

import crud, models, schemas
from database import SessionLocal, engine
models.BaseDB.metadata.create_all(bind=engine)

import jwt
import datetime

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

import os

from PIL import Image
import io

from dotenv import load_dotenv

load_dotenv()

# def list_directory_structure(root_dir, indent=''):
#     items = os.listdir(root_dir)
#     for item in items:
#         path = os.path.join(root_dir, item)
#         if os.path.isdir(path):
#             print(f"{indent}{item}/")
#             list_directory_structure(path, indent + '    ')
#         else:
#             print(f"{indent}{item}")

# root_directory = 'path_to_your_root_directory'
# list_directory_structure(str(os.getcwd()))

app = FastAPI(title="Web service Sehatyuk",
    version="0.0.1",)

app.add_middleware(
 CORSMiddleware,
 allow_origins=["*"],
 allow_credentials=True,
 allow_methods=["*"],
 allow_headers=["*"],
)


# Ensure the image directory exists
os.makedirs("image", exist_ok=True)

# Mount the image directory
app.mount("/static", StaticFiles(directory="image"), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#hapus ini kalau salt sudah digenerate
# @app.get("/getsalt")
# async def getsalt():
#     hasil = bcrypt.gensalt()
#     return {"message": hasil}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def root():
    return {"message": "Dokumentasi API: [url]/docs"}

# create user 
@app.post("/create_user/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_email = crud.get_user_by_email(db, email=user.email_user)
    db_user_no_telp = crud.get_user_by_no_telp(db, no_telp=user.no_telp_user)
    if db_user_email:
        raise HTTPException(status_code=400, detail="Error: Email sudah digunakan")
    elif db_user_no_telp:
        raise HTTPException(status_code=400, detail="Error: No telp sudah digunakan")

    return crud.create_user(db=db, user=user)


# hasil adalah akses token    
@app.post("/login_email") #,response_model=schemas.Token
async def login_email(user: schemas.UserLoginEmail, db: Session = Depends(get_db)):
    if not authenticate_by_email(db,user):
        raise HTTPException(status_code=400, detail="Username atau password tidak cocok")

    # ambil informasi username
    user_login = crud.get_user_by_email(db,user.email_user)
    if user_login:
        access_token  = create_access_token(user.email_user)
        user_id = user_login.id_user
        return {"user_id":user_id,"access_token": access_token}
    else:
        raise HTTPException(status_code=400, detail="User tidak ditemukan, kontak admin")
    
@app.post("/login_no_telp") #,response_model=schemas.Token
async def login_no_telp(user: schemas.UserLoginPhone, db: Session = Depends(get_db)):
    if not authenticate_by_no_telp(db,user):
        raise HTTPException(status_code=400, detail="Username atau password tidak cocok")

    # ambil informasi username
    user_login = crud.get_user_by_no_telp(db,user.no_telp_user)
    if user_login:
        access_token  = create_access_token(user.no_telp_user)
        user_id = user_login.id_user
        return {"user_id":user_id,"access_token": access_token}
    else:
        raise HTTPException(status_code=400, detail="User tidak ditemukan, kontak admin")


# #lihat detil user_id
@app.get("/get_user_by_id/{id_user}", response_model=schemas.User)
def read_user(id_user: int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) 
    db_user = crud.get_user(db, id_user=id_user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# update user
@app.put("/update_user/{id_user}", response_model=schemas.User)
def update_user(id_user: int, user_update: schemas.UserBase, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) 

    db_user_old = crud.get_user(db, id_user)
    db_user_email = crud.get_user_by_email(db, email=user_update.email_user)
    db_user_no_telp = crud.get_user_by_no_telp(db, no_telp=user_update.no_telp_user)
    if db_user_old.email_user != user_update.email_user:
        if db_user_email:
            raise HTTPException(status_code=400, detail="Error: Email sudah digunakan")
    if db_user_old.no_telp_user != user_update.no_telp_user:
        if db_user_no_telp:
            raise HTTPException(status_code=400, detail="Error: No telp sudah digunakan")

    db_user = crud.update_user(db, id_user, user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.put("/update_password/{id_user}", response_model= schemas.ResponseMSG)
def update_password(id_user: int, passwords: schemas.Password, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    if not match_password(db, passwords.old_password, id_user):
        raise HTTPException(status_code=400, detail="Error: Password tidak sesuai")
    update_user_password =  crud.update_password(db,id_user,passwords.new_password)
    if update_user_password:
        return JSONResponse(status_code=200, content={"message" : "Password updated successfully"})
    
@app.post("/forget_password/", response_model= schemas.ResponseMSG)
def forget_password(user_credential: schemas.UserCredential, db: Session = Depends(get_db)):
    typed_email = user_credential.email_user
    typed_phone = user_credential.no_telp_user
    typed_dob = user_credential.tgl_lahir_user
    db_user_email = crud.get_user_by_email(db, typed_email)
    if not db_user_email:
        raise HTTPException(status_code=404, detail="Email tidak ditemukan")
    else:
        db_user_phone = crud.get_user_by_no_telp(db, typed_phone)
        if not db_user_phone:
            raise HTTPException(status_code=404, detail="No. Telepon tidak ditemukan")
        else:
            if db_user_email.id_user != db_user_phone.id_user:
                raise HTTPException(status_code=404, detail="Tidak ada user dengan gabungan email dan no. telepon tersebut")
            else:
                if str(db_user_email.tgl_lahir_user) != typed_dob:
                    raise HTTPException(status_code=404, detail=f"Tanggal lahir salah")
                else:
                    if user_credential.new_password is None:
                        return JSONResponse(status_code=200, content={"message" : "Kredensial user benar"})
                    else:
                        update_user_password =  crud.update_password(db,db_user_email.id_user,user_credential.new_password)
                        if update_user_password:
                            return JSONResponse(status_code=200, content={"message" : "Password updated successfully"})
                        else:
                            raise HTTPException(status_code=500, detail="Gagal mengubah password") 


                
@app.post("/create_relasi/", response_model=schemas.Relasi ) # response_model=schemas.Cart 
def create_relasi(
    relasi: schemas.RelasiCreate, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    # print(usr)
    new_relasi = crud.create_relasi(db=db, relasi=relasi)
    return new_relasi


#ambil semua relasi milik user
@app.get("/get_relasi/{id_user}", response_model=list[schemas.Relasi])
def read_relasi(id_user:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    # print(usr)
    relasi = crud.get_relasi(db, id_user=id_user)
    return relasi

@app.get("/get_relasi_by_id/{id_relasi}", response_model=schemas.Relasi)
def read_relasi(id_relasi:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    # print(usr)
    relasi = crud.get_relasi_by_id(db, id_relasi=id_relasi)
    return relasi

@app.delete("/delete_relasi/{id_relasi}")
def delete_relasi(id_relasi:int,db: Session = Depends(get_db),token: str = Depends(oauth2_scheme) ):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    return crud.delete_relasi_by_id(db,id_relasi)

@app.post("/create_dokter/", response_model=schemas.Dokter ) # response_model=schemas.Cart 
def create_dokter(
    dokter: schemas.DokterCreate, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token)
    return crud.create_dokter(db=db, dokter=dokter)

#ambil semua dokter
@app.get("/get_dokter/", response_model=list[schemas.Dokter])
def read_dokter(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    dokter = crud.get_dokter(db, skip, limit)
    return dokter


#ambil isi dokter milik seorang user
@app.get("/get_dokter_by_id/{id_dokter}", response_model=schemas.Dokter)
def read_dokter(id_dokter:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    # print(usr)
    dokter = crud.get_dokter_by_id(db, id_dokter=id_dokter)
    return dokter

# # hapus item dokter berdasarkan dokter id
@app.delete("/delete_dokter/{id_dokter}")
def delete_dokter(id_dokter:int,db: Session = Depends(get_db),token: str = Depends(oauth2_scheme) ):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    return crud.delete_dokter_by_id(db,id_dokter)

# obat
@app.post("/create_obat/", response_model=schemas.Obat ) # response_model=schemas.Cart 
def create_obat(
    obat: schemas.ObatCreate, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    # print(usr)
    return crud.create_obat(db=db, obat=obat)

#ambil semua obat
@app.get("/get_obat/", response_model=list[schemas.Obat])
def read_obat(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    obat = crud.get_obat(db, skip, limit)
    return obat

#ambil isi obat milik seorang user
@app.get("/get_obat_by_id/{id_obat}", response_model=schemas.Obat)
def read_obat(id_obat:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    # print(usr)
    obat = crud.get_obat_by_id(db, id_obat=id_obat)
    return obat

# # hapus item obat berdasarkan obat id
@app.delete("/delete_obat/{id_obat}")
def delete_obat(id_obat:int,db: Session = Depends(get_db),token: str = Depends(oauth2_scheme) ):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    return crud.delete_obat_by_id(db,id_obat)

#ambil semua jadwal dokter
@app.get("/get_jadwal_dokter/", response_model=list[schemas.JadwalDokter])
def read_jadwal_dokter(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    jadwal_dokter = crud.get_jadwal_dokter(db, skip, limit)
    return jadwal_dokter

#ambil semua jadwal dokter berdasarkan id
@app.get("/get_jadwal_dokter_by_id/{id_dokter}", response_model=list[schemas.JadwalDokter])
def read_jadwal_dokter(id_dokter:int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    jadwal_dokter = crud.get_jadwal_dokter_by_id(db, id_dokter=id_dokter)
    return jadwal_dokter

@app.post("/create_janji_temu/", response_model=schemas.JanjiTemu ) # response_model=schemas.Cart 
def create_janji_temu(
    janji_temu: schemas.JanjiTemuCreate, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    # print(usr)
    return crud.create_janji_temu(db=db, janji_temu=janji_temu)

@app.get("/get_janji_temu/{id_user}", response_model=list[schemas.JanjiTemu])
def read_janji_temu(id_user:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    # print(usr)
    janji_temu = crud.get_janji_temu(db, id_user=id_user)
    return janji_temu

@app.get("/get_janji_temu_by_id/{id_janji_temu}", response_model=schemas.JanjiTemu)
def read_janji_temu_id(id_janji_temu:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    # print(usr)
    janji_temu = crud.get_janji_temu_by_id(db, id_janji_temu=id_janji_temu)
    return janji_temu

@app.post("/create_janji_temu_as_orang_lain/", response_model=schemas.JanjiTemuAsOrangLain ) # response_model=schemas.Cart 
def create_janji_temu_as_orang_lain(
    janji_temu_as_orang_lain: schemas.JanjiTemuAsOrangLainCreate, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) 
    return crud.create_janji_temu_as_orang_lain(db=db, janji_temu_as_orang_lain=janji_temu_as_orang_lain)

@app.get("/get_janji_temu_as_orang_lain_by_id/{id_user}", response_model=schemas.JanjiTemuAsOrangLain)
def read_janji_temu_as_orang_lain_id(id_user:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token)
    janji_temu_as_orang_lain = crud.get_janji_temu_as_orang_lain_by_id(db, id_user=id_user)
    return janji_temu_as_orang_lain

@app.put("/alter_status/{id_janji_temu}", response_model=schemas.JanjiTemu)
def alter_status(id_janji_temu:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    # print(usr)
    janji_temu = crud.alter_status(db, id_janji_temu=id_janji_temu)
    return janji_temu

@app.delete("/delete_janji_temu/{id_janji_temu}")
def delete_janji_temu(id_janji_temu:int,db: Session = Depends(get_db),token: str = Depends(oauth2_scheme) ):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    return crud.delete_janji_temu_by_id(db,id_janji_temu)

#ambil semua pengingat obat
@app.get("/get_pengingat_minum_obat/{id_user}", response_model=list[schemas.PengingatMinumObat])
def read_pengingat_minum_obat(id_user:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) #bisa digunakan untuk mengecek apakah user cocok (tdk boleh akses data user lain)
    # print(usr)
    pengingat_minum_obat = crud.get_pengingat_minum_obat(db, id_user=id_user)
    return pengingat_minum_obat

#ambil isi pengingat
@app.get("/get_pengingat_minum_obat_by_id/{id_pengingat}", response_model=schemas.PengingatMinumObat)
def read_pengingat_minum_obat(id_pengingat:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token)
    # print(usr)
    pengingat_minum_obat = crud.get_pengingat_minum_obat_by_id(db, id_pengingat=id_pengingat)
    return pengingat_minum_obat

@app.post("/create_pengingat_minum_obat/", response_model=schemas.PengingatMinumObat ) # response_model=schemas.Cart 
def create_pengingat_minum_obat(
    pengingat_minum_obat: schemas.PengingatMinumObatCreate, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) 
    return crud.create_pengingat_minum_obat(db=db, pengingat_minum_obat=pengingat_minum_obat)

# image dokter berdasarkan id
path_img = "image/"
@app.get("/dokter_image/{id_dokter}")
def read_image(id_dokter: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    usr = verify_token(token)
    dokter = crud.get_dokter_by_id(db, id_dokter)
    if not dokter:
        raise HTTPException(status_code=404, detail="id tidak valid")
    nama_image = dokter.foto_dokter
    image_path = os.path.join(path_img, "cariDokterPage", nama_image)
    if not os.path.exists(image_path):
        detail_str = f"File dengan nama {nama_image} tidak ditemukan"
        raise HTTPException(status_code=404, detail=detail_str)
    
    return FileResponse(image_path)

@app.get("/user_image/{id_user}/{image_name}")
def read_image(id_user: int, image_name: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    usr = verify_token(token)
    user = crud.get_user(db, id_user)
    if not user:
        raise HTTPException(status_code=404, detail="id tidak valid")
    image_path = os.path.join(path_img, "profilePage", image_name)
    if not os.path.exists(image_path):
        detail_str = f"File dengan nama {image_name} tidak ditemukan"
        raise HTTPException(status_code=404, detail=detail_str)
    
    return FileResponse(image_path)

@app.get("/relasi_image/{id_relasi}")
def read_image(id_relasi: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    usr = verify_token(token)
    relasi = crud.get_relasi_by_id(db, id_relasi)
    if not relasi:
        raise HTTPException(status_code=404, detail="id tidak valid")
    nama_image = relasi.foto_relasi
    image_path = os.path.join(path_img, "relasiPage", nama_image)
    if not os.path.exists(image_path):
        detail_str = f"File dengan nama {nama_image} tidak ditemukan"
        raise HTTPException(status_code=404, detail=detail_str)
    
    return FileResponse(image_path)

@app.get("/obat_image/{id_obat}")
def read_image(id_obat: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    usr = verify_token(token)
    obat = crud.get_obat_by_id(db, id_obat)
    if not obat:
        raise HTTPException(status_code=404, detail="id tidak valid")
    nama_image = obat.foto_obat
    image_path = os.path.join(path_img, "CariObatPage", nama_image)
    current_dir = os.getcwd()
    if not os.path.exists(image_path):
        detail_str = f"File dengan path {image_path} tidak ditemukan"
        raise HTTPException(status_code=404, detail=detail_str)
    
    return FileResponse(image_path)

def compress_image(image: Image.Image, quality: int = 85) -> io.BytesIO:
    img_byte_arr = io.BytesIO()
    
    if image.format == 'JPEG' or image.format == 'JPG':
        image.save(img_byte_arr, format='JPEG', quality=quality)
    elif image.format == 'PNG':
        image.save(img_byte_arr, format='PNG', optimize=True)
    else:
        raise ValueError(f"Unsupported image format: {image.format}")
    
    img_byte_arr.seek(0)
    return img_byte_arr

@app.post("/upload_user_image/{id_user}")
async def create_upload_file(
    file: UploadFile, 
    id_user: int, 
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
):
    usr = verify_token(token)
    user = crud.get_user(db, id_user)
    if not user:
        raise HTTPException(status_code=404, detail="id tidak valid")
    
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, JPG and PNG are allowed.")
    
    try:
        image = Image.open(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Retrieve the old image filename
    old_image = user.foto_user

    # Generate a new unique filename
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"

    # Compress the new image
    compressed_image = compress_image(image)

    # Define the file location
    file_location = os.path.join(path_img, "profilePage", unique_filename)
    with open(file_location, "wb") as buffer:
        buffer.write(compressed_image.getbuffer())

    # Update the user's image in the database
    success = crud.update_image_user(db, id_user, unique_filename)

    if success is not None:
        # Delete the old image if it exists
        if old_image:
            old_image_path = os.path.join(path_img, "profilePage", old_image)
            if os.path.exists(old_image_path):
                try:
                    os.remove(old_image_path)
                    print(f'Old image {old_image} deleted')
                except Exception as e:
                    print(f'Failed to delete old image {old_image}: {e}')

        return {"info": f"file '{unique_filename}' saved at '{file_location}'"}
    else:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/upload_relasi_image/{id_relasi}")
async def create_upload_file(file: UploadFile, id_relasi: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    usr = verify_token(token)
    relasi = crud.get_relasi_by_id(db, id_relasi)
    if not relasi:
        raise HTTPException(status_code=404, detail="id tidak valid")
    
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, JPG and PNG are allowed.")
    
    try:
        image = Image.open(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image file")

    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"

    compressed_image = compress_image(image)

    file_location = f"{path_img}relasiPage/{unique_filename}"
    with open(file_location, "wb") as buffer:
        buffer.write(compressed_image.getbuffer())

    success = crud.update_image_relasi(db, id_relasi, unique_filename)

    if success is not None:
        return {"info": f"file '{unique_filename}' saved at '{file_location}'"}
    else:
        raise HTTPException(status_code=500, detail="Internal Server Error")


# get rekam_medis by id
@app.get("/rekam_medis/{rekam_medis_id}", response_model=schemas.RekamMedis)
def read_rekam_medis_by_id(rekam_medis_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    usr = verify_token(token)
    db_rekam_medis = crud.get_rekam_medis_by_id(db, rekam_medis_id=rekam_medis_id)
    if db_rekam_medis is None:
        raise HTTPException(status_code=404, detail="Rekam Medis not found")
    return db_rekam_medis

# get rekam_medis by user id
@app.get("/rekam_medis/user/{user_id}/selesai", response_model=list[schemas.RekamMedis])
def read_rekam_medis_selesai_by_user(user_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    usr = verify_token(token)
    rekam_medis_list = crud.get_rekam_medis_selesai_by_user(db, user_id=user_id)
    if not rekam_medis_list:
        raise HTTPException(status_code=404, detail="No Rekam Medis found with status 'Selesai'")
    return rekam_medis_list

# periksa apakah username ada dan passwordnya cocok
# return boolean TRUE jika username dan password cocok
def authenticate_by_email(db,user: schemas.UserCreate):
    user_cari = crud.get_user_by_email(db=db, email=user.email_user)
    if user_cari:
        return (user_cari.password_user == crud.hashPassword(user.password_user))
    else:
        return False  
      
def authenticate_by_no_telp(db,user: schemas.UserCreate):
    user_cari = crud.get_user_by_no_telp(db=db, no_telp=user.no_telp_user)
    if user_cari:
        return (user_cari.password_user == crud.hashPassword(user.password_user))
    else:
        return False    
    
def match_password(db,typed_password: schemas.Password, id_user= 0, by_email= False, email_user= ""):
    if not by_email:
        user = crud.get_user(db, id_user)
    else:
        user = crud.get_user_by_email(db, email_user)
    if user:
        return user.password_user == crud.hashPassword(typed_password)
    else:
        return False

SECRET_KEY = os.getenv("SECRET_KEY")


def create_access_token(email):
    # info yang penting adalah berapa lama waktu expire
    expiration_time = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=7)    # .now(datetime.UTC)
    access_token = jwt.encode({"email":email,"exp":expiration_time},SECRET_KEY,algorithm="HS256")
    return access_token    


def verify_token(token: str):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=["HS256"])  # bukan algorithm,  algorithms (set)
        email = payload["email"]  
     
    # exception jika token invalid
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Unauthorize token, expired signature, harap login")
    except jwt.PyJWKError:
        raise HTTPException(status_code=401, detail="Unauthorize token, JWS Error")
    # except jwt.JWTClaimsError:
    #     raise HTTPException(status_code=401, detail="Unauthorize token, JWT Claim Error")
    # except jwt.JWTError:
    #     raise HTTPException(status_code=401, detail="Unauthorize token, JWT Error")   
    except Exception as e:
        raise HTTPException(status_code=401, detail="Unauthorize token, unknown error"+str(e))
    
    return {"email": email}


@app.post("/token", response_model=schemas.Token)
async def token(req: Request, form_data: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):

    f = schemas.UserCreate
    f.email_user = form_data.username
    f.password_user = form_data.password
    if not authenticate_by_email(db,f):
        raise HTTPException(status_code=400, detail="email or password tidak cocok")
 
    email_user  = form_data.username

    #buat access token\
    # def create_access_token(user_name,email,role,nama,status,kode_dosen,unit):
    access_token  = create_access_token(email_user)

    return {"access_token": access_token, "token_type": "bearer"}